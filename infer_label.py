import oscar.oscar as oscar
import pandas as pd 

df = pd.read_csv("new-labeled-data-hh.csv")
repos = pd.read_csv("repositories.csv").set_index("name")

df["link"] = ""
for index, row in df.iterrows():
    url_base = repos.loc[row["repository"], "url"]
    url = "{}/commit/{}".format(url_base, row["hash"])
    df.loc[index, "link"] = url
df["inferred_labels"] = ""

total_files = 0
unhandled_files = 0

for index, row in df.iterrows():
    commit = oscar.Commit(row["hash"])
    if len(commit.parent_shas) > 1:
        print("More than one parent: {}".format(row))
    if len(commit.parent_shas) == 0:
        print("Error: no parent {}".format(row))
    parent = oscar.Commit(commit.parent_shas[0])

    label = set()
    print("========== Commit: {}, Parent: {} ==========".format(commit.sha, parent.sha))
    print("URL: {}".format(row["link"]))
    print(commit.full_message)

    if any(x in commit.full_message.lower() for x in ["bug", "fix", "issue"]):
        label.add("fix")

    if any(x in commit.full_message.lower() for x in ["rename", "refactor"]):
        label.add("refactor")

    diffs = []
    for old_path, new_path, old_sha, new_sha in commit - parent:
        print(old_path, new_path)
        diffs.append((old_path, new_path, old_sha, new_sha))
    
    for old_path, new_path, old_sha, new_sha in diffs:
        if new_path != None:
            path = new_path.lower()
        else:
            path = old_path.lower()

        doc_suffix = [".md", ".txt", ".rst", ".html", "license", "copyright", "readme"]
        code_suffix = [".py", ".java", ".rb", ".sql", ".js"]
        chore_suffix = [".gitignore", ".gitreview" ".coveragerc", ".github", ".gitlab" 
                        "requirements.txt", "test-requirements.txt", "pylintrc",
                        ".ini", ".cfg", 
                         # Although Puppet and Shell are programming languages, 
                         #  they are often used for build and configuration,
                         #  so I think it is chore
                        ".pp", ".sh"]
        doc_folder = ["doc", "releasenote", "api-ref"]
        chore_folder = ["deployment", "conf", "manifest", "service", "meta", "task", "default", "vars", "etc", "build", "bin"]
        if "test" not in path.lower() and any(x in path for x in code_suffix):
            label.add("code")
        elif "test" in path: # Test is often spread out everywhere in the project, so I use a very loose condition
            label.add("test")
        elif any(path.endswith(x) for x in chore_suffix):
            label.add("chore")
        elif any(path.endswith(x) for x in doc_suffix):
            label.add("doc")
        elif any(path.startswith(x) for x in doc_folder):
            label.add("doc")
        elif any(path.startswith(x) for x in chore_folder):
            label.add("chore")
        else:
            print("Warning: unhandled file {}".format(path))
            unhandled_files += 1
        total_files += 1

    print("Labels for this commit: {}".format(label))
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    df.loc[index, "inferred_labels"] = ";".join(list(label))

handled_files = total_files - unhandled_files
print("{}/{} files handled({:.2f}%)".format(handled_files, total_files, handled_files * 100.0 / total_files))
df.to_csv("commits.csv", index=False, 
    columns=["company","repository","link","hash","subject","message","changed_file","label", "inferred_labels"])
