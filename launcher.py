"""
PhishGuard Launcher - Starts the proxy and Chrome browser with FULL ERROR LOGGING
Ensures mitmproxy (mitmdump) starts and listens on 127.0.0.1:8080 before launching Chrome.
Includes socket-based readiness verification and detailed debug logging.
"""
import subprocess
import sys
import os
import time
import socket
from pathlib import Path


def log_to_console_and_file(message, log_file="phishguard_launcher.log"):
    """Print to console and append to log file"""
    print(message)
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(message + '\n')
    except Exception as e:
        print(f"[Warning] Could not write to {log_file}: {e}")


def get_chrome_executable():
    """Get Chrome executable path on Windows"""
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    if os.path.exists(chrome_path):
        return chrome_path
    
    # Fallback: check 32-bit installation
    chrome_path_x86 = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    if os.path.exists(chrome_path_x86):
        return chrome_path_x86
    
    return None


def is_port_ready(host="127.0.0.1", port=8080, timeout=2):
    """
    Test if a port is listening by attempting socket connection.
    Returns True if port is reachable, False otherwise.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        return False


def wait_for_proxy_ready(host="127.0.0.1", port=8080, max_wait=20, poll_interval=1):
    """
    Poll socket connection until proxy is ready or timeout.
    Returns True if proxy became ready, False if timeout.
    """
    start_time = time.time()
    attempt = 0
    
    while time.time() - start_time < max_wait:
        attempt += 1
        if is_port_ready(host, port):
            elapsed = time.time() - start_time
            log_to_console_and_file(
                f"[PhishGuard] ✅ Proxy is READY on {host}:{port} "
                f"(detected after {elapsed:.1f}s, attempt {attempt})"
            )
            return True
        
        elapsed = time.time() - start_time
        log_to_console_and_file(
            f"[PhishGuard] ⏳ Waiting for proxy... "
            f"({elapsed:.1f}s elapsed, attempt {attempt}, retrying in {poll_interval}s)"
        )
        time.sleep(poll_interval)
    
    log_to_console_and_file(
        f"[PhishGuard] ❌ TIMEOUT: Proxy did not become ready within {max_wait} seconds"
    )
    return False


def start_proxy():
    """
    Start mitmdump with PhishGuard addon using EXACT command format.
    Captures all output to mitmproxy_debug.log for troubleshooting.
    """
    script_dir = Path(__file__).parent
    proxy_script = script_dir / "proxy_simple.py"
    debug_log = script_dir / "mitmproxy_debug.log"
    
    # EXACT command format as specified
    mitmdump_command = [
        "mitmdump",
        "-s", str(proxy_script),
        "--listen-host", "127.0.0.1",
        "--listen-port", "8080"
    ]
    
    log_to_console_and_file(
        f"\n[PhishGuard] STARTING MITMPROXY")
        
    log_to_console_and_file(
        f"[PhishGuard] Exact command: {' '.join(mitmdump_command)}"
    )
    log_to_console_and_file(
        f"[PhishGuard] Proxy script: {proxy_script}"
    )
    log_to_console_and_file(
        f"[PhishGuard] Debug log: {debug_log}"
    )
    log_to_console_and_file(
        f"[PhishGuard] Working directory: {script_dir}"
    )
    
    try:
        # Open debug log file for writing stderr/stdout
        with open(debug_log, 'w', encoding='utf-8') as debug_f:
            debug_f.write(f"=== PhishGuard mitmproxy Debug Log ===\n")
            debug_f.write(f"Timestamp: {time.ctime()}\n")
            debug_f.write(f"Command: {' '.join(mitmdump_command)}\n")
            debug_f.write(f"Working dir: {script_dir}\n")
            debug_f.write(f"Proxy script: {proxy_script}\n")
            debug_f.write(f"=====================================\n\n")
            debug_f.flush()
            
            # Start mitmdump with output capture
            proc = subprocess.Popen(
                mitmdump_command,
                stdout=debug_f,
                stderr=subprocess.STDOUT,  # Combine stderr with stdout
                cwd=str(script_dir),
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
        
        log_to_console_and_file(
            f"[PhishGuard] ✅ Subprocess launched (PID: {proc.pid})"
        )
        log_to_console_and_file(
            f"[PhishGuard] Debug output written to: {debug_log}"
        )
        
        # Small initial wait
        time.sleep(1)
        
        # Check if process is still running (didn't crash immediately)
        if proc.poll() is not None:
            log_to_console_and_file(
                f"[PhishGuard] ❌ CRITICAL: Subprocess exited immediately (exit code: {proc.returncode})"
            )
            log_to_console_and_file(
                f"[PhishGuard] Check {debug_log} for error details"
            )
            return None
        
        log_to_console_and_file(
            f"[PhishGuard] ✅ Subprocess is running (still alive)"
        )
        return proc
        
    except FileNotFoundError as e:
        log_to_console_and_file(
            f"[PhishGuard] ❌ ERROR: mitmdump not found in PATH"
        )
        log_to_console_and_file(
            f"[PhishGuard] Details: {e}"
        )
        log_to_console_and_file(
            f"[PhishGuard] Install mitmproxy using: pip install mitmproxy"
        )
        return None
    except Exception as e:
        log_to_console_and_file(
            f"[PhishGuard] ❌ ERROR: Failed to start mitmdump: {e}"
        )
        log_to_console_and_file(
            f"[PhishGuard] Exception type: {type(e).__name__}"
        )
        import traceback
        log_to_console_and_file(
            f"[PhishGuard] Traceback:\n{traceback.format_exc()}"
        )
        return None


def start_chrome(proxy_url="127.0.0.1:8080"):
    """
    Start Chrome ONLY with --proxy-server flag.
    Uses default profile, no --user-data-dir.
    """
    chrome_path = get_chrome_executable()
    
    if not chrome_path:
        log_to_console_and_file(
            f"[PhishGuard] ❌ Chrome not found at standard paths"
        )
        log_to_console_and_file(
            f"[PhishGuard] Searched: C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        )
        return None
    
    try:
        # Minimal Chrome arguments - ONLY proxy-server
        chrome_args = [
            chrome_path,
            f"--proxy-server={proxy_url}",
            "--ignore-certificate-errors",
            "--allow-insecure-localhost",
        ]
        
        log_to_console_and_file(
            f"\n[PhishGuard] STARTING CHROME"
        )
        log_to_console_and_file(
            f"[PhishGuard] Chrome path: {chrome_path}"
        )
        log_to_console_and_file(
            f"[PhishGuard] Proxy URL: {proxy_url}"
        )
        log_to_console_and_file(
            f"[PhishGuard] Chrome command: {' '.join(chrome_args)}"
        )
        
        proc = subprocess.Popen(
            chrome_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        log_to_console_and_file(
            f"[PhishGuard] ✅ Chrome launched (PID: {proc.pid})"
        )
        log_to_console_and_file(
            f"[PhishGuard] Using default user profile (no new profile created)"
        )
        log_to_console_and_file(
            f"[PhishGuard] System proxy settings: UNCHANGED"
        )
        return proc
    except Exception as e:
        log_to_console_and_file(
            f"[PhishGuard] ❌ ERROR: Failed to start Chrome: {e}"
        )
        return None


def main():
    """
    Main launcher: Start mitmdump, verify it's ready, then start Chrome.
    """
    # Clear old log
    try:
        Path("phishguard_launcher.log").unlink(missing_ok=True)
    except:
        pass
    
    log_to_console_and_file(
        "=" * 60
    )
    log_to_console_and_file(
        "PhishGuard Stage-1 MVP - Launcher Starting"
    )
    log_to_console_and_file(
        f"Timestamp: {time.ctime()}"
    )
    log_to_console_and_file(
        "=" * 60
    )
    
    # Step 1: Start mitmproxy
    log_to_console_and_file(
        "\n[STEP 1] Starting mitmproxy (mitmdump)..."
    )
    proxy_proc = start_proxy()
    
    if not proxy_proc:
        log_to_console_and_file(
            "\n[PhishGuard] ❌ CRITICAL FAILURE: Could not start mitmproxy"
        )
        log_to_console_and_file(
            "[PhishGuard] Check mitmproxy_debug.log for details"
        )
        log_to_console_and_file(
            "[PhishGuard] Exiting launcher without starting Chrome"
        )
        return 1
    
    # Step 2: Verify proxy is ready
    log_to_console_and_file(
        "\n[STEP 2] Verifying proxy is listening on 127.0.0.1:8080..."
    )
    if not wait_for_proxy_ready(max_wait=20):
        log_to_console_and_file(
            "\n[PhishGuard] ❌ CRITICAL: Proxy never became ready"
        )
        log_to_console_and_file(
            "[PhishGuard] Terminating mitmproxy and exiting"
        )
        if proxy_proc and proxy_proc.poll() is None:
            proxy_proc.terminate()
        return 1
    
    # Step 3: Start Chrome
    log_to_console_and_file(
        "\n[STEP 3] Launching Chrome with proxy configuration..."
    )
    chrome_proc = start_chrome()
    
    if not chrome_proc:
        log_to_console_and_file(
            "\n[PhishGuard] ❌ Failed to start Chrome"
        )
        log_to_console_and_file(
            "[PhishGuard] Terminating mitmproxy"
        )
        if proxy_proc:
            proxy_proc.terminate()
        return 1
    
    # Step 4: Monitor processes
    log_to_console_and_file(
        "\n[STEP 4] PhishGuard is ACTIVE and monitoring..."
    )
    log_to_console_and_file(
        "[PhishGuard] mitmproxy PID: " + str(proxy_proc.pid)
    )
    log_to_console_and_file(
        "[PhishGuard] Chrome PID: " + str(chrome_proc.pid)
    )
    log_to_console_and_file(
        "[PhishGuard] Listening on: 127.0.0.1:8080"
    )
    log_to_console_and_file(
        "[PhishGuard] (Close Chrome to exit, Ctrl+C to force stop)"
    )
    log_to_console_and_file(
        "=" * 60
    )
    
    try:
        while True:
            time.sleep(1)
            
            # Check if Chrome exited
            if chrome_proc.poll() is not None:
                log_to_console_and_file(
                    "\n[PhishGuard] Chrome closed by user"
                )
                log_to_console_and_file(
                    "[PhishGuard] Keeping proxy alive for 5 more seconds..."
                )
                time.sleep(5)
                break
            
            # Check if proxy crashed
            if proxy_proc.poll() is not None:
                log_to_console_and_file(
                    "\n[PhishGuard] ❌ ERROR: Proxy crashed unexpectedly!"
                )
                log_to_console_and_file(
                    "[PhishGuard] Check mitmproxy_debug.log for details"
                )
                break
    
    except KeyboardInterrupt:
        log_to_console_and_file(
            "\n[PhishGuard] Shutdown requested (Ctrl+C)"
        )
    
    finally:
        log_to_console_and_file(
            "\n[PhishGuard] Shutting down..."
        )
        
        # Terminate Chrome
        if chrome_proc and chrome_proc.poll() is None:
            log_to_console_and_file(
                "[PhishGuard] Terminating Chrome..."
            )
            chrome_proc.terminate()
            try:
                chrome_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                chrome_proc.kill()
        
        # Terminate proxy
        if proxy_proc and proxy_proc.poll() is None:
            log_to_console_and_file(
                "[PhishGuard] Terminating mitmproxy..."
            )
            proxy_proc.terminate()
            try:
                proxy_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proxy_proc.kill()
        
        log_to_console_and_file(
            "[PhishGuard] Protection stopped"
        )
        log_to_console_and_file(
            "[PhishGuard] System proxy settings: UNCHANGED"
        )
        log_to_console_and_file(
            "=" * 60
        )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

