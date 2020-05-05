BUF_SIZE = 60000
info = []
for chunk_index in range(0,10):
    with open('C:\\Users\\ianwa\\PycharmProjects\\Distributed-FileShare-App\\src\\monitored_files\\ians_share\\usa.png', 'rb') as file:
        file.seek(BUF_SIZE * chunk_index)
        info.append(file.read(BUF_SIZE))
for chunk_index in range(0, 10):
    with open('C:\\Users\\ianwa\\PycharmProjects\\Distributed-FileShare-App\\src\\monitored_files\\ians_share\\test.png', 'r+b') as file2:
        file2.seek(BUF_SIZE * chunk_index)
        file2.write(info[chunk_index])

# with open('C:\\Users\\ianwa\\PycharmProjects\\Distributed-FileShare-App\\src\\monitored_files\\ians_share\\usa.png', 'rb') as file:
#     print(file.read())
