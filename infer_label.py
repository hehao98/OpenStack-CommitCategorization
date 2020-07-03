from collections import Counter
import oscar.oscar as oscar
import pandas as pd 

df = pd.read_csv("new-labeled-data-hh.csv")
repos = pd.read_csv("repositories.csv").set_index("name")

df["link"] = ""
for index, row in df.iterrows():
    url_base = repos.loc[row["repository"], "url"]
    url = "{}/commit/{}".format(url_base, row["hash"])
    df.loc[index, "link"] = url
df["commit_labels"] = ""
df["file_labels"] = ""

total_files = 0
unhandled_files = 0

for index, row in df.iterrows():
    commit = oscar.Commit(row["hash"])
    if len(commit.parent_shas) > 1:
        print("More than one parent: {}".format(row))
    if len(commit.parent_shas) == 0:
        print("Error: no parent {}".format(row))
    parent = oscar.Commit(commit.parent_shas[0])

    commit_labels = set()
    file_labels = Counter()
    print("=" * 50)
    print("Commit: {}, Parent: {}".format(commit.sha, parent.sha))
    print("URL: {}".format(row["link"]))
    print(commit.full_message)

    if any(x in commit.full_message.lower() for x in ["implement", "blueprint"]):
        commit_labels.add("feature")
    if any(x in commit.full_message.lower() for x in ["bug", "fix", "issue", "error", "fail"]):
        commit_labels.add("fix")
    if any(x in commit.full_message.lower() for x in ["renam", "refactor", "replac"]):
        commit_labels.add("refactor")
    if any(x in commit.full_message.lower() for x in ["remov", "deprecat", "stop"]):
        commit_labels.add("deprecate")

    diffs = []
    for old_path, new_path, old_sha, new_sha in commit - parent:
        path = ""
        if new_path != None:
            path = new_path.lower()
        else:
            path = old_path.lower()

        doc_suffix = [".md", ".txt", ".rst", ".html", "license", "copyright", "readme", "authors", "maintainers"]
        code_suffix = [".py", ".java", ".sql", ".js"]
        build_suffix = [".gitignore", ".gitreview", ".coveragerc",
                        "requirements.txt", "test-requirements.txt", "pylintrc",
                        "tox.ini"]
        # Although Puppet and Shell are programming languages, 
        #  they are often used for build and configuration,
        #  so I think it is for deployment
        deploy_suffix = [".yaml", ".yml", ".cfg", ".rb", ".pp", ".sh", ".conf", ".j2"]               
        doc_folder = ["doc", "releasenote", "api-ref"]
        build_folder = [".github", ".gitlab", ".travis", "build", "bin"]
        deploy_folder = ["deploy", "conf", "manifest", "devstack", "task", "service", "etc"]

        label = ""
        # check folder first
        if "test" in path and "test-requirements.txt" not in path: # Test is often spread out everywhere in the project, so I use a very loose condition
            label = "test"
        elif any(path.startswith(x) for x in doc_folder):
            label = "doc"
        elif any(path.startswith(x) for x in build_folder):
            label = "build"
        elif any(path.startswith(x) for x in deploy_folder):
            label = "deploy"
        # then file suffix
        elif any(path.endswith(x) for x in code_suffix):
            label = "code"
        elif any(path.endswith(x) for x in build_suffix):
            label = "build"
        elif any(path.endswith(x) for x in deploy_suffix):
            label = "deploy"
        elif any(path.endswith(x) for x in doc_suffix):
            label = "doc"
        else:
            print("Warning: unhandled file {}".format(path))
            unhandled_files += 1
            label = "unknown"
        file_labels[label] += 1
        total_files += 1
        print(old_path, new_path, label)

    print("Labels for this commit: {}".format(commit_labels))
    print("+" * 50)
    df.loc[index, "commit_labels"] = ";".join(list(commit_labels))
    df.loc[index, "file_labels"] = ";".join(["{}-{}".format(x, y) for x, y in file_labels.items()])

handled_files = total_files - unhandled_files
print("{}/{} files handled({:.2f}%)".format(handled_files, total_files, handled_files * 100.0 / total_files))
df.to_csv("commits.csv", index=False, 
    columns=["company","repository","link","hash","subject","message","changed_file","commit_labels","file_labels"])
