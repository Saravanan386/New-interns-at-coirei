import glob

for f in glob.glob('app/routers/*.py'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if 'current_user["id"]' in content:
        new_content = content.replace('current_user["id"]', 'current_user["user_id"]')
        with open(f, 'w', encoding='utf-8') as out_file:
            out_file.write(new_content)
        print(f"Fixed matching keys in {f}")
