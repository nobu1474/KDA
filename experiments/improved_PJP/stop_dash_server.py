import os
import subprocess

def stop_dash_server(port=8050):
    """Dashサーバーなどで使用中のポートを見つけて強制終了する。"""
    try:
        # lsofコマンドで指定ポートを使っているプロセスID(PID)を取得
        # -t はPIDのみ出力、-i:{port} は指定ポートを使用中のプロセス
        result = subprocess.run(
            ['lsof', '-t', f'-i:{port}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        pids = result.stdout.strip().split('\n')
        pids = [pid for pid in pids if pid]  # 空文字を除去
        
        if not pids:
            print(f"Port {port} を使用しているプロセスは見つかりませんでした。")
            return
            
        for pid in pids:
            try:
                os.kill(int(pid), 9)  # SIGKILL (強制終了)
                print(f"Port {port} を使用中のプロセス (PID: {pid}) を終了しました。")
            except ProcessLookupError:
                print(f"PID: {pid} は既に見つかりません。")
            except PermissionError:
                print(f"PID: {pid} の強制終了に必要な権限がありません。")
                
    except Exception as e:
        print(f"プロセスの終了中にエラーが発生しました: {e}")

if __name__ == "__main__":
    PORT = 8050
    print(f"==== 停止処理開始 (Port: {PORT}) ====")
    stop_dash_server(PORT)
    print("==== 停止処理完了 ====")
