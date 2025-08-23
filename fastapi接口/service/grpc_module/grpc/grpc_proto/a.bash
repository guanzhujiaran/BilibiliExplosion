source ../../../../../venv/bin/activate
echo "Deleting existing .py files..."
find . -name "*.py" -type f -delete
echo "Compiling .proto files..."
find . -name "*.proto" -type f | while read proto_file; do
    python -m grpc_tools.protoc \
        --proto_path=. \
        --python_out=. \
        --grpc_python_out=. \
        "$proto_file"
done

echo "Done."