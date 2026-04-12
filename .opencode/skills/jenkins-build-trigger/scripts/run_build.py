#!/usr/bin/env python3
"""
Jenkins Build Trigger Client
用于与 Jenkins 服务器交互，执行构建任务的相关操作
"""

import json
import argparse
import sys
import os

# 配置路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(ROOT_DIR, 'config.json')

def load_config():
    """从配置文件读取 Jenkins 连接信息"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
            jenkins_config = config.get('jenkins', {})
            return (
                jenkins_config.get('url', 'http://localhost:8080'),
                jenkins_config.get('username', ''),
                jenkins_config.get('token', '')
            )
    except FileNotFoundError:
        print(f"警告：配置文件 {CONFIG_PATH} 不存在，使用默认值")
        return ('http://localhost:8080', '', '')
    except json.JSONDecodeError as e:
        print(f"错误：配置文件格式错误：{e}")
        sys.exit(1)

# 从配置文件加载 Jenkins 连接信息
JENKINS_URL, JENKINS_USERNAME, JENKINS_TOKEN = load_config()

try:
    import jenkins
except ImportError:
    print("错误：未安装 python-jenkins 库")
    print("请运行：pip install python-jenkins")
    sys.exit(1)


def get_jenkins_connection():
    """创建 Jenkins 连接对象"""
    if JENKINS_USERNAME and JENKINS_TOKEN:
        server = jenkins.Jenkins(JENKINS_URL, username=JENKINS_USERNAME, password=JENKINS_TOKEN)
    else:
        server = jenkins.Jenkins(JENKINS_URL)
    return server


def list_jobs(server, parent_path=''):
    """列出所有 Pipeline 任务（包括文件夹中的任务）"""
    try:
        # Use get_all_jobs() to get all jobs including those in folders
        all_jobs = server.get_all_jobs()
        
        pipeline_jobs = []
        valid_colors = ['blue', 'red', 'yellow', 'green', 'grey', 'disabled', 'aborted', 'notbuilt', 'unstable']
        
        for job in all_jobs:
            # job['fullname'] contains the full path like 'folder/job_name' or just 'job_name'
            full_name = job['fullname']
            
            # Get job info to check color/status
            try:
                job_info = server.get_job_info(full_name)
                color = job_info.get('color', '')
                
                if any(color.startswith(c) for c in valid_colors):
                    pipeline_jobs.append({
                        'name': full_name,
                        'full_name': full_name,
                        'color': color
                    })
            except Exception:
                # If we can't get job info, try to get basic info
                # Just add the job if we can't determine its color
                pipeline_jobs.append({
                    'name': full_name,
                    'full_name': full_name,
                    'color': ''
                })
        
        return pipeline_jobs
    except Exception:
        # Fallback to the original method if get_all_jobs fails
        try:
            jobs = server.get_jobs()
        except Exception:
            jobs = []
        
        pipeline_jobs = []
        valid_colors = ['blue', 'red', 'yellow', 'green', 'grey', 'disabled', 'aborted', 'notbuilt', 'unstable']
        
        for job in jobs:
            full_name = job['name']
            is_folder = '_class' in job and 'Folder' in job['_class']
            
            if is_folder:
                # Get jobs from folder using folder info
                try:
                    folder_info = server.get_job_info(full_name)
                    if 'jobs' in folder_info:
                        for sub_job in folder_info['jobs']:
                            sub_full_name = f"{full_name}/{sub_job['name']}"
                            sub_color = sub_job.get('color', '')
                            
                            if any(sub_color.startswith(c) for c in valid_colors):
                                pipeline_jobs.append({
                                    'name': sub_full_name,
                                    'full_name': sub_full_name,
                                    'color': sub_color
                                })
                except Exception:
                    pass
                
                # Recursively check nested folders
                nested_jobs = list_jobs_from_folder(server, full_name)
                pipeline_jobs.extend(nested_jobs)
            else:
                color = job.get('color', '')
                if any(color.startswith(c) for c in valid_colors):
                    pipeline_jobs.append({
                        'name': full_name,
                        'full_name': full_name,
                        'color': color
                    })
        
        return pipeline_jobs

def list_jobs_from_folder(server, parent_path):
    """辅助函数：从特定父路径列出任务"""
    try:
        # Get folder info to find sub-jobs
        folder_info = server.get_job_info(parent_path)
        pipeline_jobs = []
        valid_colors = ['blue', 'red', 'yellow', 'green', 'grey', 'disabled', 'aborted', 'notbuilt', 'unstable']
        
        if 'jobs' in folder_info:
            for sub_job in folder_info['jobs']:
                full_name = f"{parent_path}/{sub_job['name']}"
                is_folder = '_class' in sub_job and 'Folder' in sub_job['_class']
                
                if is_folder:
                    # Recursive call for nested folders
                    nested_jobs = list_jobs_from_folder(server, full_name)
                    pipeline_jobs.extend(nested_jobs)
                else:
                    color = sub_job.get('color', '')
                    if any(color.startswith(c) for c in valid_colors):
                        pipeline_jobs.append({
                            'name': full_name,
                            'full_name': full_name,
                            'color': color
                        })
        
        return pipeline_jobs
    except Exception:
        return []


def get_job_params(server, job_name):
    """获取任务的构建参数"""
    try:
        job_info = server.get_job_info(job_name)
        params = []
        
        if not job_info:
            return params
        
        # 查找包含参数定义的 property
        for prop in job_info.get('property', []):
            if 'parameterDefinitions' in prop:
                for param_def in prop['parameterDefinitions']:
                    param_info = {
                        'name': param_def.get('name', ''),
                        'type': param_def.get('type', 'unknown'),
                        'default': param_def.get('defaultParameterValue', {}).get('value', ''),
                        'description': param_def.get('description', '')
                    }
                    
                    if param_def.get('type') == 'choice':
                        param_info['choices'] = param_def.get('choices', [])
                    
                    if param_info['name']:
                        params.append(param_info)
                break
        
        return params
    except Exception as e:
        print(f"获取参数失败：{e}")
        return []


def build_job(server, job_name, parameters=None, use_token=True):
    """触发任务构建"""
    try:
        # For Jenkins folder jobs, we need to handle the build differently
        # If parameters are provided, use them
        if parameters is not None and len(parameters) > 0:
            build_number = server.build_job(job_name, parameters=parameters)
        else:
            # When no parameters provided, we have two options:
            # 1. Try to get default parameters from job definition
            # 2. Call build job without parameters (may fail for folder jobs)
            try:
                # Try to get the default values from job parameters
                job_params = get_job_params(server, job_name)
                if job_params:
                    # Build a dict with default values
                    default_params = {}
                    for param in job_params:
                        if param.get('default'):
                            default_params[param['name']] = param['default']
                    if default_params:
                        build_number = server.build_job(job_name, parameters=default_params)
                    else:
                        # No defaults, try with empty dict
                        build_number = server.build_job(job_name, parameters={})
                else:
                    # No parameters defined in job, try with empty dict
                    build_number = server.build_job(job_name, parameters={})
            except:
                # If getting job params fails, try the basic build
                build_number = server.build_job(job_name, parameters={})
        
        # Properly format the job name for URL construction
        url_job_name = job_name.replace('/', '/job/')
        if not url_job_name.startswith('job/'):
            url_job_name = f"job/{url_job_name}"
        
        return {
            'success': True,
            'job_name': job_name,
            'build_number': build_number,
            'url': f"{JENKINS_URL}/{url_job_name}/{build_number}/"
        }
    except Exception as e:
        # If the standard approach fails, return error
        return {
            'success': False,
            'error': str(e)
        }


def main():
    parser = argparse.ArgumentParser(description='Jenkins Build Trigger Client')
    parser.add_argument('command', choices=['list', 'params', 'build'], help='要执行的操作')
    parser.add_argument('--job', '-j', type=str, help='任务名称')
    parser.add_argument('--param', '-p', action='append', metavar=('NAME', 'VALUE'), 
                       help='构建参数 (可多次使用)', nargs=2)
    parser.add_argument('--json', '-o', action='store_true', help='以 JSON 格式输出')
    
    args = parser.parse_args()
    
    try:
        server = get_jenkins_connection()
    except Exception as e:
        error_result = {'success': False, 'error': f'无法连接到 Jenkins: {e}'}
        if args.json:
            print(json.dumps(error_result, indent=2, ensure_ascii=False))
        else:
            print(f"错误：无法连接到 Jenkins 服务器\n详情：{e}")
        sys.exit(1)
    
    if args.command == 'list':
        jobs = list_jobs(server)
        result = {
            'success': True,
            'count': len(jobs),
            'jobs': jobs
        }
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if not jobs:
                print("没有找到任何构建任务")
            else:
                print(f"找到 {len(jobs)} 个构建任务:\n")
                for i, job in enumerate(jobs, 1):
                    print(f"  {i}. {job['name']}")
    
    elif args.command == 'params':
        if not args.job:
            error_result = {'success': False, 'error': '需要指定任务名称 (--job)'}
            if args.json:
                print(json.dumps(error_result, indent=2, ensure_ascii=False))
            else:
                print("错误：需要指定任务名称")
            sys.exit(1)
        
        params = get_job_params(server, args.job)
        result = {
            'success': True,
            'job_name': args.job,
            'parameters': params
        }
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if not params:
                print(f"任务 '{args.job}' 没有构建参数")
            else:
                print("任务 '{}' 的构建参数:\n".format(args.job))
                for param in params:
                    default_str = " (默认：{})".format(param['default']) if param['default'] else ""
                    desc_str = " - {}".format(param.get('description')) if param.get('description') else ""
                    print("  * {}: {}{}".format(param['name'], param['type'], default_str))
                    if param['type'] == 'choice' and param.get('choices'):
                        print("    选项：{}".format(', '.join(param['choices'])))
                    if desc_str:
                        print("    {}".format(desc_str.strip()))
    
    elif args.command == 'build':
        if not args.job:
            error_result = {'success': False, 'error': '需要指定任务名称 (--job)'}
            if args.json:
                print(json.dumps(error_result, indent=2, ensure_ascii=False))
            else:
                print("错误：需要指定任务名称")
            sys.exit(1)
        
        params_dict = None
        if args.param:
            params_dict = {name: value for name, value in args.param}
        
        result = build_job(server, args.job, params_dict)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if result['success']:
                print("[OK] 成功触发构建任务：{}".format(result['job_name']))
                print("  构建编号：{}".format(result['build_number']))
                print("  构建链接：{}".format(result['url']))
            else:
                print("[FAIL] 构建失败：{}".format(result['error']))
                sys.exit(1)


if __name__ == '__main__':
    main()
