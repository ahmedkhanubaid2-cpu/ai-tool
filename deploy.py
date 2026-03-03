import paramiko
import tarfile
import os
import sys

# Parameters
HOST = '187.77.129.112'
USER = 'root'
PASSWORD = '5LOI;OtaVu9H@-Zv'
REMOTE_DIR = '/var/www/ai-tool/'
TAR_NAME = 'deploy.tar.gz'
LOCAL_TAR_PATH = TAR_NAME

def create_tar():
    print("Creating tarball...")
    with tarfile.open(LOCAL_TAR_PATH, "w:gz") as tar:
        for item in os.listdir('.'):
            if item in ['.git', 'venv', 'node_modules', '.gemini', 'deploy.tar.gz', '__pycache__', 'data']:
                continue
            if item == 'storybook-ai':
                # Manually add storybook-ai to exclude venv inside it
                for root, dirs, files in os.walk(item):
                    if 'venv' in root or '__pycache__' in root or '.pytest_cache' in root:
                        continue
                    for file in files:
                        file_path = os.path.join(root, file)
                        tar.add(file_path)
            elif item == 'storybook-ui':
                for root, dirs, files in os.walk(item):
                    if 'node_modules' in root or 'dist' in root:
                        continue
                    for file in files:
                        file_path = os.path.join(root, file)
                        tar.add(file_path)
            else:
                tar.add(item)
    print("Tarball created.")

def upload_and_deploy():
    print(f"Connecting to {HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(HOST, username=USER, password=PASSWORD, timeout=10)
        
        print("Uploading tarball...")
        sftp = ssh.open_sftp()
        try:
            sftp.stat(REMOTE_DIR)
        except IOError:
            sftp.mkdir(REMOTE_DIR)
            
        sftp.put(LOCAL_TAR_PATH, REMOTE_DIR + TAR_NAME)
        sftp.close()
        
        print("Extracting and applying updates...")
        commands = [
            f"cd {REMOTE_DIR} && tar -xzf {TAR_NAME}",
            f"pkill -f uvicorn || true",
            f"pkill -f vite || true",
            # Start backend
            f"cd {REMOTE_DIR}/storybook-ai && [ ! -d venv ] && python3 -m venv venv || true",
            f"cd {REMOTE_DIR}/storybook-ai && ./venv/bin/pip install -r ../requirements.txt uvicorn fastapi python-multipart python-dotenv openai pandas python-docx pillow docx google-genai",
            f"cd {REMOTE_DIR}/storybook-ai && nohup ./venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 > backend.log 2>&1 &",
            # Start frontend
            f"cd {REMOTE_DIR}/storybook-ui && npm install",
            f"cd {REMOTE_DIR}/storybook-ui && nohup npm run dev -- --host 0.0.0.0 --port 3000 > frontend.log 2>&1 &"
        ]
        
        for cmd in commands:
            print(f"Executing: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            out = stdout.read().decode('utf-8')
            err = stderr.read().decode('utf-8')
            if out: print(f"Output: {out.strip()}")
            if err: print(f"Error: {err.strip()}")
            
        print("Deployment finished!")
    except Exception as e:
        print(f"Deployment failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    create_tar()
    upload_and_deploy()
