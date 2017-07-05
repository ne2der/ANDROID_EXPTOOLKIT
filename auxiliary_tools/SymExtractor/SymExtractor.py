import sys
import binascii
import struct

#magic_addr = ["00100800c0ffffff00100800c0ffffff00100800c0ffffff"]
magic_addr = ["00000800c0ffffff40000800c0ffffff80000800c0ffffff"]

size = 8


def init_kernel_static(img, imgbase):
    loc = img.find(magic_addr[0].decode("hex"))
    if loc == -1:
        print "can not find magic_addr to locate addresses list head"
        return
    addresses = struct.unpack_from("<Q", img, loc)
    offset = 0

    #find address list start through magic address
    while addresses[0]:
        offset = offset + 1
        if loc + offset * 8 >= len(img):
            print "can not find end of addresses list"
            return
        addresses = struct.unpack_from("<Q", img, loc - offset * 8)
    # print hex(addresses[0])
    addresses_offset = loc - 8 * (offset - 1)
    print "addresses list start at offset %x" % addresses_offset
    offset = 1
    addresses = struct.unpack_from("<Q", img, loc + offset * 8)



    while addresses[0] > 0xffffffc000000000:
        offset = offset + 1
        if loc + offset * 8 >= len(img):
            print "can not find end of addresses list"
            return
        addresses = struct.unpack_from("<Q", img, loc + offset * 8)
    
    #skip zero between address_list and 
    while addresses[0] == 0:
        offset = offset + 1
        if loc + offset * 8 >= len(img):
            print "can not find end of addresses list"
            return
        addresses = struct.unpack_from("<I", img, loc + offset * 8)
 

    loc = loc + offset*8
    sym_num = addresses[0]
    print "sym num %d " % sym_num

    #skip zero between addresses list and sym name
    offset = 1
    addresses = struct.unpack_from("<Q", img, loc + offset * 8)

    while addresses[0] == 0:
        offset =offset + 1
        addresses = struct.unpack_from("<Q", img, loc + offset * 8)
    sym_name_offset = loc+offset*8
    print "sym_name_offset %x" % sym_name_offset

    loc = sym_name_offset
    offset = 1
    addresses = struct.unpack_from("B", img, loc + offset )
    print "first",addresses[0]
    while addresses[0] != 0:
        offset = offset + 1
        if loc + offset  >= len(img):
            print "out of range when try to find all sym_name"
            return
        addresses = struct.unpack_from("B", img, loc + offset )
    offset = 0
    for i in range(sym_num):
        symlen = struct.unpack_from("B", img, loc + offset )
        offset = offset + symlen[0] + 1
        if loc + offset  >= len(img):
            print "out of range when try to find all sym_name"
            return

    sym_name_end = offset+loc-1

    #skip zero

    loc = sym_name_end
    offset = 1

    addresses = struct.unpack_from("B", img, loc + offset )
    while addresses[0] == 0:
        offset = offset + 1
        if loc + offset >= len(img):
            print "out of range when try to find markers start"
            return
        addresses = struct.unpack_from("B", img, loc + offset)


    #alignment  markers always start with 0
    markers_offset = (loc+offset)-0x8
    loc = markers_offset
    offset=1
    addresses = struct.unpack_from("<Q", img, loc + offset*8)
    while addresses[0] != 0:
        offset = offset + 1
        if loc + offset >= len(img):
            print "out of range when try to find all markers"
            return
        addresses = struct.unpack_from("<Q", img, loc + offset*8)

    while addresses[0] == 0:
        offset = offset + 1
        if loc + offset >= len(img):
            print "out of range when try to find sym_token_table"
            return
        addresses = struct.unpack_from("B", img, loc + offset*8)

    sym_token_table_offset = loc+offset*8

    loc = sym_token_table_offset
    offset = 1
    addresses = struct.unpack_from("<Q", img, loc + offset * 8)
    while addresses[0] != 0:
        offset = offset + 1
        if loc + offset >= len(img):
            print "out of range when try to find end of sym token table"
            return
        addresses = struct.unpack_from("<Q", img, loc + offset * 8)

    while addresses[0] == 0:
        offset = offset + 1
        if loc + offset >= len(img):
            print "out of range when try to find sym_token_index"
            return
        addresses = struct.unpack_from("<Q", img, loc + offset * 8)

    #sym_token_index start with 0x0000
    sym_token_index=loc+offset*8
    nameoff=0
    sym=''
    f = open("res",'w')

    for i in range(sym_num):
        namelen= struct.unpack_from("BB", img, sym_name_offset + nameoff)[0]

        for j in range(namelen):
            tmp=struct.unpack_from("B", img, sym_name_offset + nameoff+1+j)[0]
            tmpindex=struct.unpack_from("h", img, sym_token_index + tmp*2)[0]





            symchar = struct.unpack_from("B", img, sym_token_table_offset+tmpindex)[0]


            while symchar!=0:

                sym = sym + chr(symchar)
                tmpindex = tmpindex + 1
                symchar = struct.unpack_from("B", img, sym_token_table_offset + tmpindex)[0]

        #print sym, hex(struct.unpack_from("<Q", img, addresses_offset + i * 8)[0])
        f.writelines(sym[1:]+" "+sym[0]+" "+hex(struct.unpack_from("<Q", img, addresses_offset + i * 8)[0])+'\n')
        sym=''
                #sym = sym+struct.unpack_from("s", img, sym_token_table_offset+tmpindex)[0]




        nameoff = nameoff + namelen+1
    print hex(loc+offset*8)





def main(imgpath, imgbase):
    f = open(imgpath, "r")
    img = f.read()
    f.close()
    print hex(len(img))
    init_kernel_static(img, imgbase)


def usage():
    print "python SymExtractor <kernel.img> <32|64>"


if __name__ == '__main__':
    argn = len(sys.argv)
    if argn < 3:
        usage()
        exit()
    elif argn >= 3:
        if sys.argv[2] == 64:
            main(sys.argv[1], 0xffffffc000080000)
        else:
            main(sys.argv[1], 0xc0008000)
