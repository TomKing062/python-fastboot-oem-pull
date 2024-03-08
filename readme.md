# python-fastboot-oem-pull

Use libusb

Install (hacky)

1. install [python-adb](https://github.com/google/python-adb) by`python setup.py install`
2. `pip uninstall adb`
3. copy adb folder in this project to `$PYTHON_INSTALL_DIR/Lib/site-packages/adb`

Usage:

1. **python main.py oem pull partition** – would return the partition table
2. **python main.py oem pull \*partition_name\*** – would return the contents of *partition_name* (g. oem pull uboot_log)
3. **python main.py oem pull \*address\*++\*size\*** – would return the contents of the memory *address*, returning *size* bytes. (g. oem pull 0x80000000++0x1000)
4. **python main.py reboot**