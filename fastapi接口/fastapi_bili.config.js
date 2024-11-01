module.exports = {
  apps : [{
		name: 'fastapi-app-bili',
		script: './fastapi接口/请求代理_ver_database_fastapi.py',
		cwd:'K:/python test',
		interpreter: 'C:/ProgramData/miniconda3/envs/Bili310/python.exe',
		instances: 1,
		wait_ready: true,
		exec_mode: "fork",
		autorestart: true,
		watch: false,
		out_file: "/dev/null",
   		error_file: "/dev/null"
  },
	{
		name: 'fastapi-bili-other-scripts',
		script: './fastapi接口/scripts/start_other_service.py',
		cwd:'K:/python test',
		interpreter: 'C:/ProgramData/miniconda3/envs/Bili310/python.exe',
		instances: 1,
		wait_ready: true,
		exec_mode: "fork",
		autorestart: true,
		watch: false,
		out_file: "/dev/null",
   		error_file: "/dev/null"
	}
  		]
};