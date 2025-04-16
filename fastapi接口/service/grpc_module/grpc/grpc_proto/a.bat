for /r %i in (*.proto) do python -m grpc_tools.protoc --proto_path=E:\grpcparse\bilibili-API-collect\grpc_api --python_out=. --grpc_python_out=. %i

