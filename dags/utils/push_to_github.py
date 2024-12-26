from github import Github, InputGitAuthor
from datetime import datetime

def push_to_github(local_file_path, repo_file_path):
    # Tu token de acceso personal de GitHub
    token = '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'

    # Autenticación con tu cuenta de GitHub
    g = Github(token)
    usuario = 'migpaniag'
    repositorio = 'EPGS'
    repo_name = f'{usuario}/{repositorio}'
    repo = g.get_repo(repo_name)

    # Contenido que quieres subir al archivo
    with open(local_file_path, 'r', encoding='utf8') as file:
        file_content = file.read()

    # Commit de la subida
    datetime_now = datetime.now()
    commit_message = f'Update "{datetime_now.strftime("%Y-%m-%d %H:%M")}"'

    # Autor del commit (opcional)
    author = InputGitAuthor(usuario, 'miguel.elokim@gmail.com')

    try:
        # Verificar si el archivo ya existe
        try:
            file = repo.get_contents(repo_file_path, ref='main')
            # Si el archivo existe, lo actualizamos
            repo.update_file(file.path, commit_message, file_content, file.sha, branch='main', author=author)
            print("Archivo actualizado correctamente.")
        except:
            # Si el archivo no existe, lo creamos
            repo.create_file(repo_file_path, commit_message, file_content, branch='main', author=author)
            print("Archivo subido correctamente.")
    except Exception as e:
        print(f"Error: {e}")
