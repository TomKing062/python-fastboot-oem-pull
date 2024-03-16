# python-fastboot-oem-pull

Use libusb

Install

1. `pip install pycryptodome`
2. `pip install libusb1`
3. (windows) copy libusb-1.0.dll to C:\Windows\System32\ (i use [MSYS2-MINGW64 one](https://mirror.msys2.org/mingw/mingw64/mingw-w64-x86_64-libusb-1.0.27-1-any.pkg.tar.zst))
4. (some version python need this, some not) copy adb folder in this project to `$PYTHON_INSTALL_DIR/Lib/site-packages/adb`

Usage:

1. **python main.py oem pull partition** – would return the partition table
2. **python main.py oem pull \*partition_name\*** – would return the contents of *partition_name* (g. oem pull uboot_log)
3. **python main.py oem pull \*address\*++\*size\*** – would return the contents of the memory *address*, returning *size* bytes. (g. oem pull 0x80000000++0x1000)
4. **python main.py reboot**
