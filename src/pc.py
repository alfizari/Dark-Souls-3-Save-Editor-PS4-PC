## ALL THIS SCRIPT IS FROM JTESTA AT GITHUB: https://github.com/jtesta/souls_givifier. A MODFIED VERSION OF THE SCRIPT TO HANDE DECRYPT AND ENCRYPT OF THE DS2 SL2 FILES.
#ALL THE CREDIT GOES TO JTESTA and Nordgaren: https://github.com/Nordgaren/ArmoredCore6SaveTransferTool


import os
import sys
import struct
import hashlib
from tkinter import ttk, filedialog, messagebox, simpledialog, Scrollbar
import tkinter as tk
from typing import Optional, Dict
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from typing import Optional


# nightreign sl2 key
DS2_KEY = b'\xfd\x46\x4d\x69\x5e\x69\xa3\x9a\x10\xe3\x19\xa7\xac\xe8\xb7\xfa'

DEBUG_MODE = True
input_file = None

def bytes_to_intstr(byte_array: bytes) -> str:
    ret = ''
    for _, i in enumerate(byte_array):
        ret += "%u," % i
    return ret[0:-1]


def debug(msg: str = '') -> None:
    if DEBUG_MODE:
        print(msg)


def calculate_md5(data: bytes) -> bytes:
    return hashlib.md5(data).digest()


def remove_pkcs7_padding(data: bytes) -> bytes:
    """Remove PKCS7 padding from decrypted data."""
    if not data:
        raise ValueError("Data is empty, cannot remove padding.")
    pad_len = data[-1]
    if pad_len == 0 or pad_len > 16:
        raise ValueError(f"Invalid PKCS7 padding byte: {pad_len}")
    # Validate all padding bytes are correct
    if data[-pad_len:] != bytes([pad_len] * pad_len):
        raise ValueError("Invalid PKCS7 padding — padding bytes are inconsistent.")
    return data[:-pad_len]


def add_pkcs7_padding(data: bytes, block_size: int = 16) -> bytes:
    """Add PKCS7 padding so data length is a multiple of block_size."""
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)


# Data layout (mirrors the C# reference):
#   [ 0:16 ]  checksum  — MD5 of everything from byte 16 onward  (IV + encrypted payload)
#   [16:32 ]  IV        — AES-CBC initialisation vector
#   [32:   ]  encrypted payload
CHECKSUM_OFFSET = 0
CHECKSUM_SIZE   = 16
IV_OFFSET       = 16
IV_SIZE         = 16
PAYLOAD_OFFSET  = 32   # encrypted payload starts here


class BND4Entry:
    def __init__(self, raw_data: bytes, index: int, output_folder: str,
                 size: int, offset: int, name_offset: int,
                 footer_length: int, data_offset: int):
        self.index         = index
        self._index        = index
        self.size          = size
        self.data_offset   = data_offset
        self.footer_length = footer_length
        self._raw_data     = raw_data
        self.decrypted     = False

        # Full entry blob (checksum + IV + encrypted payload)
        self._entry_blob = raw_data[offset:offset + size]

        self._decrypted_slot_path = output_folder
        self._name       = f"USERDATA_{index:02d}"
        self._clean_data = b''

        # Pull IV from the correct offset (bytes 16-32)
        self._iv = self._entry_blob[IV_OFFSET:IV_OFFSET + IV_SIZE]
        # Encrypted payload starts at byte 32
        self._encrypted_payload = self._entry_blob[PAYLOAD_OFFSET:]

    # ------------------------------------------------------------------
    # Decrypt — strips PKCS7 padding before writing to disk
    # ------------------------------------------------------------------
    def decrypt(self) -> None:
        try:
            decryptor = Cipher(
                algorithms.AES(DS2_KEY), modes.CBC(self._iv)
            ).decryptor()
            decrypted_padded = (
                decryptor.update(self._encrypted_payload) + decryptor.finalize()
            )

            # Strip PKCS7 padding so the file on disk is the raw game data
            self._clean_data = remove_pkcs7_padding(decrypted_padded)

            if self._decrypted_slot_path:
                os.makedirs(self._decrypted_slot_path, exist_ok=True)
                output_path = os.path.join(self._decrypted_slot_path, self._name)
                with open(output_path, 'wb') as f:
                    f.write(self._clean_data)

            self.decrypted = True

        except Exception as e:
            print(f"Error decrypting entry {self._index}: {str(e)}")
            raise

    # ------------------------------------------------------------------
    # Encrypt + sign  (matches C# SetEncryptedData exactly)
    # Re-adds PKCS7 padding before encrypting.
    # ------------------------------------------------------------------
    def encrypt_sl2_data(self) -> bytes:
        """
        Pad _clean_data with PKCS7, encrypt with the stored IV, then build:
          [0:16]  MD5( IV + encrypted_payload )   <- checksum
          [16:32] IV
          [32:]   encrypted payload

        This matches the C# reference:
            checksum = md5.ComputeHash(data, 16, data.Length - 16)
            Array.Copy(checksum, 0, data, 0, 16)
        i.e. checksum = MD5( data[16:] ) = MD5( IV + encrypted_payload )
        """
        # Re-add PKCS7 padding before encrypting so the ciphertext length
        # matches the original block-aligned encrypted payload exactly.
        padded_data = add_pkcs7_padding(self._clean_data)

        encryptor = Cipher(
            algorithms.AES(DS2_KEY), modes.CBC(self._iv)
        ).encryptor()
        encrypted_payload = (
            encryptor.update(padded_data) + encryptor.finalize()
        )

        # Checksum covers IV + encrypted payload  (data[16:] in the C# code)
        iv_plus_payload = self._iv + encrypted_payload
        checksum = hashlib.md5(iv_plus_payload).digest()

        return checksum + iv_plus_payload   # [checksum][IV][payload]

    # ------------------------------------------------------------------
    # patch_checksum is no longer needed – the checksum is computed fresh
    # inside encrypt_sl2_data() on the *encrypted* data, exactly as the
    # C# reference does.  Kept as a no-op so nothing breaks if called.
    # ------------------------------------------------------------------
    def patch_checksum(self):
        pass   # checksum is written by encrypt_sl2_data()


import json


def process_entries_in_order(entries):
    sorted_entries = sorted(entries, key=lambda e: e.index)
    for entry in sorted_entries:
        entry.decrypt()
    return sorted_entries


def save_index_mapping(entries, output_path):
    mapping = {}
    for entry in entries:
        if entry.decrypted:
            filename = f"USERDATA_{entry.index:02d}"
            mapping[entry.index] = filename

    mapping_file = os.path.join(output_path, "index_mapping.json")
    with open(mapping_file, 'w') as f:
        json.dump(mapping, f)


def get_input() -> Optional[str]:
    return filedialog.askopenfilename(
        title="Select Decrypted SL2 File",
        filetypes=[("SL2 Files", "*.sl2"), ("All Files", "*.*")]
    )


def decrypt_ds2_sl2(input_file, directory, log_callback=None) -> Dict[int, str]:
    global original_sl2_path
    global input_decrypted_path
    global bnd4_entries
    global raw

    if not input_file:
        input_file = get_input()

    if not input_file:
        return None

    original_sl2_path = input_file

    def log(message):
        if log_callback:
            log_callback(message)
        debug(message)

    try:
        with open(input_file, 'rb') as f:
            raw = f.read()
    except Exception as e:
        log(f"ERROR: Could not read input file: {e}")
        return {}

    log(f"Read {len(raw)} bytes from {input_file}.")
    if raw[0:4] != b'BND4':
        log("ERROR: 'BND4' header not found! This doesn't appear to be a valid SL2 file.")
        return {}
    else:
        log("Found BND4 header.")

    num_bnd4_entries = struct.unpack("<i", raw[12:16])[0]
    log(f"Number of BND4 entries: {num_bnd4_entries}")

    unicode_flag = (raw[48] == 1)
    log(f"Unicode flag: {unicode_flag}")
    log("")

    BND4_HEADER_LEN       = 64
    BND4_ENTRY_HEADER_LEN = 32

    bnd4_entries = []
    successful_decryptions = 0

    script_dir    = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(script_dir, directory)
    input_decrypted_path = output_folder

    for i in range(num_bnd4_entries):
        pos = BND4_HEADER_LEN + (BND4_ENTRY_HEADER_LEN * i)

        if pos + BND4_ENTRY_HEADER_LEN > len(raw):
            log(f"Warning: File too small to read entry #{i} header")
            break

        entry_header = raw[pos:pos + BND4_ENTRY_HEADER_LEN]

        if entry_header[0:8] != b'\x50\x00\x00\x00\xff\xff\xff\xff':
            log(f"Warning: Entry header #{i} does not match expected magic value - skipping")
            continue

        entry_size          = struct.unpack("<i", entry_header[8:12])[0]
        entry_data_offset   = struct.unpack("<i", entry_header[16:20])[0]
        entry_name_offset   = struct.unpack("<i", entry_header[20:24])[0]
        entry_footer_length = struct.unpack("<i", entry_header[24:28])[0]

        if entry_size <= 0 or entry_size > 1_000_000_000:
            log(f"Warning: Entry #{i} has invalid size: {entry_size} - skipping")
            continue

        if entry_data_offset <= 0 or entry_data_offset + entry_size > len(raw):
            log(f"Warning: Entry #{i} has invalid data offset: {entry_data_offset} - skipping")
            continue

        if entry_name_offset <= 0 or entry_name_offset >= len(raw):
            log(f"Warning: Entry #{i} has invalid name offset: {entry_name_offset} - skipping")
            continue

        try:
            entry = BND4Entry(
                raw_data=raw,
                index=i,
                output_folder=output_folder,
                size=entry_size,
                offset=entry_data_offset,
                name_offset=entry_name_offset,
                footer_length=entry_footer_length,
                data_offset=entry_data_offset,
            )
            entry.decrypt()
            bnd4_entries.append(entry)
            successful_decryptions += 1

        except Exception as e:
            log(f"Error processing entry #{i}: {str(e)}")
            continue

    save_index_mapping(bnd4_entries, input_decrypted_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), directory   )


def get_output() -> Optional[str]:
    filename = filedialog.asksaveasfilename(
        title="Save Encrypted SL2 File As",
        filetypes=[("SL2 Files", "*.sl2"), ("All Files", "*.*")],
        defaultextension=".sl2",
        initialfile="DS2SOFS0000.sl2"
    )
    if filename:
        print(f"Selected output SL2 file: {filename}")
        return filename
    return None


raw = b''


def read_input():
    global input_file, raw

    if not input_file:
        print("ERROR: input_file is not set. Call decrypt_ds2_sl2() first.")
        sys.exit(1)

    original_sl2_path = input_file

    with open(original_sl2_path, 'rb') as f:
        raw = f.read()

    debug("Read %u bytes from %s." % (len(raw), original_sl2_path))

    if raw[0:4] != b'BND4':
        print("ERROR: 'BND4' header not found!")
        sys.exit(-1)
    else:
        debug("Found BND4 header.")

    num_bnd4_entries = struct.unpack("<i", raw[12:16])[0]
    unicode_flag     = (raw[48] == 1)

    return raw, num_bnd4_entries, unicode_flag


slot_occupancy        = {}
bnd4_entries          = []
BND4_HEADER_LEN       = 64
BND4_ENTRY_HEADER_LEN = 32


def encrypt_modified_files(output_sl2_file, directory):
    global raw, bnd4_entries, original_sl2_path

    with open(original_sl2_path, 'rb') as f:
        original_data = f.read()

    new_data      = bytearray(original_data)
    script_dir    = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(script_dir, directory)

    for entry in bnd4_entries:
        filename  = f"USERDATA_{entry.index:02d}"
        file_path = os.path.join(output_folder, filename)

        if not os.path.exists(file_path):
            continue

        with open(file_path, 'rb') as f:
            modified_data = f.read()

        entry._clean_data = bytearray(modified_data)

        # encrypt_sl2_data() re-adds PKCS7 padding and handles signing internally:
        #   result = MD5(IV + encrypted_payload) + IV + encrypted_payload
        encrypted_entry_data = entry.encrypt_sl2_data()

        if len(encrypted_entry_data) != entry.size:
            print(f"  WARNING: Size mismatch! Expected {entry.size}, got {len(encrypted_entry_data)}")
            continue

        data_start = entry.data_offset
        new_data[data_start:data_start + len(encrypted_entry_data)] = encrypted_entry_data

    with open(output_sl2_file, 'wb') as f:
        f.write(new_data)