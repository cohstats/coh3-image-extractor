import struct
import texture2ddecoder
from PIL import Image
import zlib
import os

# WebP conversion quality setting (0-100)
WEBP_QUALITY = 85

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


def find_zlib_header(bytes_tdat):
    """
    Find the first zlib header in the data.
    Returns the offset of the first zlib header, or -1 if not found.
    """
    for i in range(len(bytes_tdat) - 1):
        if bytes_tdat[i] == 0x78 and bytes_tdat[i+1] in [0x01, 0x5e, 0x9c, 0xda]:
            return i
    return -1


def try_decompress_mipped(bytes_tdat):
    """
    Try multiple decompression strategies for mipped files.
    Returns: (first_chunk, unused_data) or raises exception if all fail.
    """
    # Strategy 1: Standard offset 16
    try:
        d = zlib.decompressobj()
        result = d.decompress(bytes_tdat[16:])
        return (result, d.unused_data)
    except:
        pass

    # Strategy 2: Find first zlib header
    try:
        offset = find_zlib_header(bytes_tdat)
        if offset >= 0:
            d = zlib.decompressobj()
            result = d.decompress(bytes_tdat[offset:])
            return (result, d.unused_data)
    except:
        pass

    # Strategy 3: Offset 0
    try:
        d = zlib.decompressobj()
        result = d.decompress(bytes_tdat)
        return (result, d.unused_data)
    except:
        pass

    raise Exception("All decompression strategies failed for mipped file")


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

        # Unpack the width and height from the byte data.
        
        # The new struct fields in version 6 can be ignored as the real issue
        # happens when the zlib decompress step tries with the unused data with some files (no idea why).
        
        tman_header = struct.unpack("<iiiiiiiiiii", bytes_tman[:44]) # unpack to 11 * 32bit ints
        uk1, width, height, _uk2, _uk3, texture_compression, mip_count, _uk4, mip_texture_count, size_uncompressed, size_compressed = tman_header
    
        try:
            # Check if file is mipped first to determine decompression approach
            is_mipped = os.path.basename(file_path_src).lower().endswith('_mipped.rrtex') or '_mipped.' in os.path.basename(file_path_src).lower()

            if is_mipped:
                # For mipped files, try multiple decompression strategies
                first_chunk, unused_data = try_decompress_mipped(bytes_tdat)

                # Process the first chunk - it might have a header
                # Try to detect if there's a 16-byte header
                if len(first_chunk) >= 16:
                    # Check if first 12 bytes look like a mip header (mip_level, width, height)
                    try:
                        potential_mip_level, potential_width, potential_height = struct.unpack('<III', first_chunk[:12])
                        # If values are reasonable, assume it's a header
                        if potential_mip_level < 20 and potential_width <= 4096 and potential_height <= 4096:
                            decompressed_chunks = [first_chunk[16:]]
                        else:
                            decompressed_chunks = [first_chunk]
                    except:
                        decompressed_chunks = [first_chunk]
                else:
                    decompressed_chunks = [first_chunk]

                # Process remaining chunks
                remaining_data = unused_data
                chunk_count = 1
                max_chunks = 20  # Safety limit

                while len(remaining_data) > 0 and chunk_count < max_chunks:
                    try:
                        # Find the next zlib header
                        found_header = False
                        for i in range(len(remaining_data) - 1):
                            if remaining_data[i] == 0x78 and remaining_data[i+1] in [0xda, 0x9c, 0x01, 0x5e]:
                                if i > 0:
                                    remaining_data = remaining_data[i:]
                                found_header = True
                                break

                        if not found_header:
                            break

                        Next_decompressor = zlib.decompressobj()
                        chunk = Next_decompressor.decompress(remaining_data)
                        decompressed_chunks.append(chunk)
                        remaining_data = Next_decompressor.unused_data
                        chunk_count += 1

                    except Exception:
                        break

                # Calculate the size of the first mipmap level (highest resolution)
                if texture_compression == 28:  # BC7
                    block_size = 16
                elif texture_compression == 22:  # BC3
                    block_size = 16
                elif texture_compression == 19 or texture_compression == 18:  # BC1
                    block_size = 8
                else:
                    raise Exception(f"Unknown texture compression type: {texture_compression}")

                width_mip = max(1, width)
                height_mip = max(1, height)
                num_blocks = ((width_mip + 3) // 4) * ((height_mip + 3) // 4)
                mip0_size = num_blocks * block_size

                # Try to find mip level 0 chunk
                mip0_chunk = None
                for chunk in decompressed_chunks:
                    if len(chunk) >= 16:
                        try:
                            mip_level, chunk_width, chunk_height = struct.unpack('<III', chunk[:12])
                            if mip_level == 0 and chunk_width == width and chunk_height == height:
                                mip0_chunk = chunk
                                break
                        except:
                            continue

                if mip0_chunk is not None:
                    # Extract mip0 data (skip the 16-byte header)
                    if len(mip0_chunk) >= 16 + mip0_size:
                        decompressed_data = mip0_chunk[16:16 + mip0_size]
                    else:
                        decompressed_data = mip0_chunk[16:]
                        if len(decompressed_data) < mip0_size:
                            decompressed_data += b'\x00' * (mip0_size - len(decompressed_data))
                else:
                    # Fallback: use the first/largest chunk
                    if len(decompressed_chunks) > 0:
                        # Try first chunk
                        if len(decompressed_chunks[0]) >= mip0_size:
                            decompressed_data = decompressed_chunks[0][:mip0_size]
                        else:
                            # Concatenate all chunks and take what we need
                            all_data = b''.join(decompressed_chunks)
                            decompressed_data = all_data[:mip0_size]
                            if len(decompressed_data) < mip0_size:
                                decompressed_data += b'\x00' * (mip0_size - len(decompressed_data))

            else:
                # Original implementation for non-mipped files
                Decompressor = zlib.decompressobj()
                # get the first decompressed chunk
                chunk = Decompressor.decompress(bytes_tdat[16:])    # magic shift by 16
                decompressed_chunks = [chunk[16:]]                  # create list, another magic shift by 16
                # unused compressed data
                unused_data = Decompressor.unused_data

                # while there are still unused_data(not decompressed), try decompressing them, otherwise assign it directly.
                try:
                    while len(unused_data) > 0:
                        Next_decompressor = zlib.decompressobj()
                        chunk = Next_decompressor.decompress(unused_data)
                        decompressed_chunks.append(chunk)
                        unused_data = Next_decompressor.unused_data

                    # assemble decompressed_data from decompressed_chunks
                    decompressed_data = b''
                    for chunk in decompressed_chunks:
                        decompressed_data += chunk
                except:
                    # assemble decompressed_data from decompressed_chunks
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

            # Save with format-specific options
            file_ext = os.path.splitext(file_path_dest)[1].lower()
            if file_ext == '.webp':
                # Save as WebP with quality setting, preserving transparency
                dec_img.save(file_path_dest, 'WEBP', quality=WEBP_QUALITY, lossless=False)
            else:
                # For TGA, PNG and other formats, use default settings
                dec_img.save(file_path_dest)

        except Exception as e:      
            error = f"convert_rrtex failed.\nException: {e}"
            print(error)
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