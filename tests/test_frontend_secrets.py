import os
import glob

def test_frontend_bundle_does_not_leak_secrets():
    """
    Ensure the frontend static build does not contain backend secrets.
    """
    # Assuming frontend is built to a dist/ or build/ directory, or we check the raw src
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
    
    # Check all files in frontend directory (including built files if they exist)
    forbidden_keys = [
        "RAZORPAY_KEY_SECRET",
        "CAPABILITY_SIGNING_KEY",
        "REDIS_URL"
    ]
    
    found_secrets = []
    
    # We will just do a simplistic recursive search
    for root, dirs, files in os.walk(frontend_dir):
        # Exclude node_modules to speed up
        if "node_modules" in dirs:
            dirs.remove("node_modules")
            
        for file in files:
            if file.endswith((".ts", ".tsx", ".js", ".jsx", ".html", ".css")):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        for key in forbidden_keys:
                            if key in content:
                                found_secrets.append(f"Secret {key} found in {filepath}")
                except Exception:
                    pass
                    
    assert not found_secrets, f"Frontend secret leak detected:\\n" + "\\n".join(found_secrets)
