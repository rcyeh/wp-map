## Proto

Proto files enable high performance writing, transmitting, and reading of data.

### Decision: Use protobufs.

`protoc -I=. --python_out=../proces/ --plugin=protoc-gen-ts=../node_modules/.bin/protoc-gen-ts --ts_out=../docs/ ./wpmaps.proto

`cd ../docs; npx tsc wpmaps.ts --target es2022 --module esnext`


