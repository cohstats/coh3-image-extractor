import struct
import texture2ddecoder
from PIL import Image
import zlib

def print_bytes_data(byte_data):
    for i in range(0, len(byte_data), 4):
        try:
            int32 = struct.unpack("<i",byte_data[i:i+4])[0]
        except:
            int32 = -1
            pass
        print(byte_data[i:i+4],end='')
        print('\t\t\t',end='')
        print(int32)

    
def get_data_positions(buffer, data):
    """
    Finds the starting and ending positions of the `data` bytes in the `buffer` bytes.

    Args:
        buffer (bytes): The byte buffer to search.
        data (bytes): The bytes to search for in the buffer.
    """
    found_pos = buffer.find(data)
    return (found_pos, found_pos+len(data))
    

def convert_rrtex(file_path_src: str, file_path_dest: str) -> None:
    with open(file_path_src, "rb") as f:
        # Read the entire file into a byte buffer
        buff = f.read()  
        # find the start and end of "DATATMAN" and "DATATDAT" sections
        tman_start, tman_end = get_data_positions(buff, b"DATATMAN") 
        tdat_start, tdat_end = get_data_positions(buff, b"DATATDAT")
        # get the tman and tdat bytes
        bytes_tman = buff[tman_end+12 : tdat_start]
        bytes_tdat = buff[tdat_end:]

        # Unpack the width and height from the byte data
        tman_header = struct.unpack("<iiiiiiiiiii", bytes_tman[:44]) # unpack to 11 * 32bit ints
        _, width, height, _, _, texture_compression, mip_count, _, mip_texture_count , size_uncompressed , size_compressed  = tman_header

        try:
            Decompressor = zlib.decompressobj()
            # get the first decompressed chunk
            chunk = Decompressor.decompress(bytes_tdat[16:])    # magic shift by 16
            decompressed_chunks = [chunk[16:]]                  # create list, another magic shift by 16
            # unused compressed data
            unused_data = Decompressor.unused_data

            # while there are still unused_data(not decompressed), try decompressing them
            while len(unused_data) > 0:
                Next_decompressor = zlib.decompressobj()
                chunk = Next_decompressor.decompress(unused_data)
                decompressed_chunks.append(chunk)
                unused_data = Next_decompressor.unused_data

            # assamble decompressed_data from decompressed_chunks
            decompressed_data = b''
            for chunk in decompressed_chunks:
                decompressed_data += chunk

            # decode with correct texture compression. Data are decoded to BGRA
            if texture_compression == 28:
                decoded_data= texture2ddecoder.decode_bc7(decompressed_data, width, height)
            elif texture_compression == 22:
                decoded_data= texture2ddecoder.decode_bc3(decompressed_data, width, height)
            elif texture_compression == 19:
                decoded_data= texture2ddecoder.decode_bc1(decompressed_data, width, height) # Bc1
            elif texture_compression == 18:
                decoded_data= texture2ddecoder.decode_bc1(decompressed_data, width, height) # Bc1 with alpha?  
            else:
                # unsupported 2(R)
                raise Exception(f"Unknown texture compression type: {texture_compression}")

            dec_img = Image.frombytes("RGBA", (width, height), decoded_data, 'raw', ("BGRA"))
            dec_img.save(file_path_dest)

        except Exception as e:      
            error = f"convert_rrtex failed.\nException: {e}"
            raise Exception(error)

# #################################
# This is a test code
# if __name__ == "__main__":
#
#
#     file_path_src = "C:/coh-data/coh3/in/assault_engineer_us_portrait.rrtex"
#     file_path_dest ="C:/coh-data/coh3/out/assault_engineer_us_portrait.tga"
#     convert_rrtex(file_path_src, file_path_dest)
#     print('saved!')
#