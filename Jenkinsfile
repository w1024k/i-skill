pipeline {
    agent any

    parameters {
        string(name: 'MESSAGE', defaultValue: 'Hello, Jenkins!', description: '输入要打印的消息')
    }

    stages {
        stage('Hello') {
            steps {
                echo params.MESSAGE
            }
        }
    }
}