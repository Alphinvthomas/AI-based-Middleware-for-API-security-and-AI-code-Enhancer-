from github_integration import GitHubIntegration

client = GitHubIntegration('AswinRaj1123', 'RentMate')
print('Getting code files...')
code_files = client.get_all_code_files()
print(f'Found {len(code_files)} code files')

if code_files:
    # Try to fetch the backend JavaScript file which should have APIs
    backend_js = 'backend/node_server.js'
    if backend_js in code_files:
        print(f'\nTrying to fetch: {backend_js}')
        content = client.get_file_content(backend_js)
        if content:
            print(f'✅ Successfully fetched file! Content length: {len(content)} characters')
            print(f'First 300 characters:\n{content[:300]}')
        else:
            print(f'❌ Failed to fetch content')
    else:
        print(f'{backend_js} not found in list')

