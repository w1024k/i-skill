按照以下要求创建skills，你有不明白的地方可以让我补充
- 调用jenkins的构建任务使用
- 提前使用python-jenkins创建脚本
- 如果用户没有说明需要构建的任务，列出所有的任务让用户选择，用户可以输入序号或者名称，
- 要遍历每一级文件夹，找到所有的任务，如果任务有别名或者备注要展示出来
- 接着通过预创的脚本查询pipeline的参数，让用户选择参数， 如果参数有别名或者备注要展示出来
- 如果用户直接直接说出了构建任务和参数，利用大模型根据语义解析任务名称和参数，你调用脚本查询任务和参数进行匹配
- 最后,执行构建前，必须写出任务名称和参数，让用户确定，用户确定后直接调用预置的脚本，调用构建任务
- 在SKILL.md同级目录下，包含以下脚本定义
  script/list_jobs.py
  script/get_job_params.py
  script/build_job.py
  config.json
  script/base.py (初始化jenkins连接,从config.json中读取连接信息,放公共函数)
- 在config.json中配置jenkins的地址和用户名密码， 如果没有配置，使用时要提醒用户配置
- 说明清楚脚本和配置文件的文字,使用opencode,codex,claude code,trae等工具都可以用这个skill,都可以快速找到对应的脚本和配置文件
- SKILL.md使用中文
- 支持windows powershell和cmd中运行