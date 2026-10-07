import os
import sys
import argparse
from ftplib import FTP

def main():
    parser = argparse.ArgumentParser(description="Upload compiled mksh via FTP")
    parser.add_argument("--ip", required=True, help="FTP server IP address")
    parser.add_argument("--user", default="root", help="FTP username")
    parser.add_argument("--password", default="root", help="FTP password")
    parser.add_argument("--local", default=r"H:\workspace\mksh\build\ARM64_GENERIC\Release\strip\mksh", help="Local file path")
    parser.add_argument("--remote", default="/bin/mksh", help="Remote target path")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.local):
        print(f"Error: Local file does not exist: {args.local}")
        sys.exit(1)
        
    print(f"Connecting to FTP server at {args.ip}...")
    try:
        ftp = FTP(args.ip, timeout=10)
        ftp.login(args.user, args.password)
        print("FTP Login successful.")
        
        file_size = os.path.getsize(args.local)
        print(f"Uploading {args.local} ({file_size} bytes) to {args.remote}...")
        
        with open(args.local, 'rb') as f:
            ftp.storbinary(f'STOR {args.remote}', f)
            
        print("Upload completed successfully!")
        ftp.quit()
    except Exception as e:
        print(f"Upload failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
