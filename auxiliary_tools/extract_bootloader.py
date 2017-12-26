import sys, struct, os

def main():

    #Reading the commandline arguments
    if len(sys.argv) != 3:
        print "USAGE: %s bootloader.img output_path" % __file__
        return
    bootloader_path = sys.argv[1]
    output_path = sys.argv[2]

    #Verifying the magic
    bootloader_file = open(bootloader_path, 'rb')
    data = bootloader_file.read()
    bootloader_file.close()
    magic = data[0:8]
    print hex(struct.unpack(">I",magic[0:4])[0])
    if struct.unpack(">I",magic[0:4])[0] == 0x3cd61ace:
        extract_2(data,output_path)
        return

    elif struct.unpack(">I",magic[4:8])[0] == 0x70617274:
        extract_3(data,output_path)
        return

    elif magic == "BOOTLDR!":
        extract_1(data,output_path)
        return
    else:
        print "Can not handle ,check releasetools.py in AOSP"






def extract_1(data,output_path):
    #Reading in the metadata block
    point = 8
    image_num,start_addr,size = struct.unpack("<III", data[point:point+12])
    print " image_num %, start_addr %08X, size: %08X" % (image_num, start_addr, size)
    image_metadata = []
    point = point +12
    file_start = start_addr
    for i in range(0, image_num):
        file_name = file_name = ext_string(data,point)
        file_size = struct.unpack("<I", data[point+0x40:point+0x40+4])[0]
        f = open(os.path.join(output_path, file_name), 'wb')
        tmpdata = data[file_start:file_start + file_size]
        f.write(tmpdata)
        f.close()
        point = point + 0x44
        file_start = file_start+file_size





def extract_2(data,output_path):

    point = 8
    version = ext_string(data,point)

    i = 0
    while 1:
        point = 0x4c + i*0x50
        file_name = ext_string(data,point)
        print file_name
        if file_name == '':
            break
        file_start, = struct.unpack("<I" ,data[point+ 0x48:point+0x48+4])
        file_size, = struct.unpack("<I", data[point + 0x4c:point + 0x4c + 4])
        i = i+1
        print hex(file_start),hex(file_size)
        f = open(os.path.join(output_path,file_name),'wb')
        tmpdata = data[file_start:file_start+file_size]
        f.write(tmpdata)
        f.close()
    print "version:%s" % version

def extract_3(data,output_path):
    # #define BOOTLDR_MAGIC "MBOOTV1"
    # #define HEADER_SIZE 1024
    # #define SECTOR_SIZE 512
    # device/google/shamu/releasetools.py

    HEADER_SIZE = 1024
    SECTOR_SIZE = 512

    point = 4

    while 1:
        point = point +  0x20
        print hex(point)
        file_name = ext_string(data,point)
        print file_name
        if file_name == '':
            break
        file_start = struct.unpack("<I", data[point + 0x18:point + 0x18 + 4])[0]* SECTOR_SIZE + HEADER_SIZE
        file_end = struct.unpack("<I", data[point + 0x1c:point + 0x1c + 4])[0]* SECTOR_SIZE + HEADER_SIZE
        print file_start,file_end
        f = open(os.path.join(output_path, file_name), 'wb')
        tmpdata = data[file_start:file_end]
        f.write(tmpdata)
        f.close()




    print 'extract_3'



def ext_string(data,point):
    s = ''
    c, = struct.unpack('b',data[point:point+1])
    i = 0
    while c != 0:
        s = s + chr(c)
        i= i+1
        c, = struct.unpack('b',data[point+i:point+1+i])
    return s



if __name__ == "__main__":
    main()