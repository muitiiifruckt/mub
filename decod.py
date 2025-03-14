# Пример данных
packet_data = bytes.fromhex("02 00 00 00 45 00 00 2d cc d5 40 00 80 06 00 00 7f 00 00 01 7f 00 00 01 ea ca 13 88 e9 9d bd f2 4a 3f f6 fc 50 18 20 03 79 cd 00 00 66 73 64 61 66")

# Декодируем полезную нагрузку (последние 5 байт)
payload = packet_data[-5:].decode('ascii')
print("Полезная нагрузка:", payload)  # Вывод: fsdaf