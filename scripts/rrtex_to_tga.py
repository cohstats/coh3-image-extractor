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
                print("Processing mipped file")
                # For mipped files, we need to handle multiple zlib streams properly
                Decompressor = zlib.decompressobj()
                # get the first decompressed chunk
                chunk = Decompressor.decompress(bytes_tdat[16:])    # magic shift by 16
                decompressed_chunks = [chunk[16:]]                  # create list, another magic shift by 16
                # unused compressed data
                unused_data = Decompressor.unused_data

                # while there are still unused_data(not decompressed), try decompressing them
                remaining_data = unused_data
                chunk_count = 1
                max_chunks = 20  # Safety limit

                while len(remaining_data) > 0 and chunk_count < max_chunks:
                    try:
                        # For mipped files, we need to find the next zlib header
                        # as there might be padding between compressed blocks
                        found_header = False
                        for i in range(len(remaining_data) - 1):
                            if remaining_data[i] == 0x78 and remaining_data[i+1] in [0xda, 0x9c, 0x01, 0x5e]:
                                if i > 0:
                                    # Skip padding bytes to get to the zlib header
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
                        # If decompression fails, stop trying
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

                # For mipped files, each decompressed chunk contains a mip level with a 16-byte header
                # The header format is: [mip_level (4 bytes), width (4 bytes), height (4 bytes), ...]
                # We need to find the chunk with mip_level = 0 (highest resolution)
                mip0_chunk = None

                for chunk in decompressed_chunks:
                    if len(chunk) >= 16:
                        # Parse the 16-byte header to get mip level, width, height
                        try:
                            mip_level, chunk_width, chunk_height = struct.unpack('<III', chunk[:12])
                            # Check if this is mip level 0 and matches our expected dimensions
                            if mip_level == 0 and chunk_width == width and chunk_height == height:
                                mip0_chunk = chunk
                                break
                        except:
                            # If header parsing fails, continue to next chunk
                            continue

                if mip0_chunk is not None:
                    # Extract mip0 data (skip the 16-byte header)
                    if len(mip0_chunk) >= 16 + mip0_size:
                        decompressed_data = mip0_chunk[16:16 + mip0_size]
                    else:
                        # If chunk is smaller than expected, use what we have after the header
                        decompressed_data = mip0_chunk[16:]
                        # Pad with zeros if necessary (shouldn't happen with valid files)
                        if len(decompressed_data) < mip0_size:
                            decompressed_data += b'\x00' * (mip0_size - len(decompressed_data))
                else:
                    # Fallback: use the largest chunk (old behavior for compatibility)
                    if len(decompressed_chunks) > 1:
                        largest_chunk = max(decompressed_chunks, key=len)
                        if len(largest_chunk) >= 16 + mip0_size:
                            # Skip the 16-byte header and take exactly mip0_size bytes
                            decompressed_data = largest_chunk[16:16 + mip0_size]
                        elif len(largest_chunk) >= mip0_size:
                            # If largest chunk is exactly mip0_size, use it directly (no header)
                            decompressed_data = largest_chunk[:mip0_size]
                        else:
                            # Last resort: assemble all chunks and take first mip0_size bytes
                            # This was the source of the duplication bug - avoid if possible
                            print("Warning: Using fallback concatenation method for mipped file")
                            decompressed_data = b''.join(decompressed_chunks)[:mip0_size]
                    else:
                        # Single chunk, take first mip0_size bytes
                        decompressed_data = decompressed_chunks[0][:mip0_size]

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