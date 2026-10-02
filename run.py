import os
import sys
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    
    # Allow passing port via argument: python run.py 8080 or python run.py --port 8080
    args = sys.argv[1:]
    if "--port" in args:
        idx = args.index("--port")
        if idx + 1 < len(args) and args[idx + 1].isdigit():
            port = int(args[idx + 1])
    elif args and args[0].isdigit():
        port = int(args[0])

    print("=" * 60)
    print(" Claim Verification & AI Detection Engine")
    print(f" Running at: http://127.0.0.1:{port}")
    print("=" * 60)

    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=port, reload=True)
