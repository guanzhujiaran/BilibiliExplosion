# wsl开发环境下可能导致docker_vol里面的文件的权限有问题,数据库无法加载对应的库,每次启动前需要设置一下权限问题
chmod -R 777 ./docker_vol/mysql_data/data
chmod -R 777 ./docker_vol/postgres
