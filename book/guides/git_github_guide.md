# Git and GitHub Guide

Git is a version control software. Watched contents are organized as "repos" (short for repositories), and a repo is essentially a folder with a special (and hidden) `.git` directory. Git *could* be use purely locally, but a repo usually has a remote (cloud) copy also. GitHub is a common place to store such remote copies.

## Conceptual introduction to git

Local files on a Git repo can be in one of 3 states: untracked (no version control), tracked but uncommitted (changes are watched but not permanently recorded), and committed (changes are recorded). When a file is modified (including new file creation and existing file deletion), the changes are initially untracked. To track those changes, a `git add`  command needs to be issued on those files. And to permanently record the changes, a `git commit` command needs to be issued, which make a snapshot of all the currently tracked files in the repo.

To create the local repo from a remote repo, use `git clone`. To sync any updates on the remote repo to the local repo, use `git pull`. To sync any committed updates on the local repo to the remote repo, use `git push`. 

![Architecture of git](img/git_architecture.png)

## Walkthrough of key git commands

The commands below are available in the Terminal interface.

+ `git status`: Show the current status of the local repo. Importantly, this will list the files that are untracked and tracked but uncommitted.

+ `git add <pathspec>`: Add the files specified by `<pathspec>` to the collection of tracked files. Usually `<pathspec>` is either the path of a specific folder (relative to the top of the git repo), or a single dot (`.`), which add all untracked files to the collection of tracked files.

+ `git commit -m <message>`: Commit all the changed tracked files to permanent record. The message is used to summarize the major changes between the previous snapshot and the new snapshot, and is usually put in double quotes.

+ `git push <dest>`: Push the current snapshot to the remote repo. Most commonly `<dest>` is `origin` (no quotes), which is the location of where the repo is cloned from.

+ `git pull <source>`: Pull the current snapshot stored in the remote repo. Most commonly `<source>` is `origin`.

+ `git clone <repository>`: Clone the remote repo `<repository>` to the local filesystem. To get the correct url of `<repository>` on GitHub, navigate to the repo, click on the "Code <>" button, and use the copy icon to copy the https url to the repo.

![screenshot of cloning from GitHub repo](img/git_clone_GItHub.png)

## Advanced usage: branching and merge

For projects with a single developer, the above commands and usage pattern is often sufficient. However, when a project has multiple members, it is important to avoid conflicts between the work of different members, or at least to resolve them in an orderly manner. The main tool to do so in git is **branches**. Essentially, each branch of a repo serves as a distinct chain of records that do not interfere with other branches. Each branch can thus be used to develop specific set of features of the repo, and when the a set of feature is ready, it can be merged back to the main branch.

The main commands associated with branching are:

+ `git branch <branch_name>`: Create a new branch called `<branch_name>`
+ `git checkout <branch_name>`: Switch the branch that the current development is following to the branch `<branch_name>`
+ `git merge <branch_name>`: Merge the currently followed branch to the branch `<branch_name>`. Usually `<branch_name>` is `main`.

Note that when `git merge` is executed sometimes the merge will fail and because of conflicts, and these conflicts have to be resolved manually by editing the conflicted files.

A common development pattern is to have a small number of members (often a single person) specializing in merge management. When the other members completed their feature development, they commit their branch to the remote repo and make a **pull request** that notify the merge specialist to merge their development branch to the main branch. In that way teh merge process itself will not create extra conflicts.

For more information about git commands, the official documentations and additional resources can be found on [https://git-scm.com/](https://git-scm.com/)

## Graphical user interface for Git on JupyterLab

Our jupyterlab is built with the `jupyter-git` extension included. On the left panel of JupyterLab there is a tab with the Git logo. When your file navigator is pointing at folder outside of a git repo, the left panel will give you the option to clone a remote repo. If your file navigator is pointing at a location inside a git repo, the lef panel will give you the option to add, commit, push, and pull files, as well as the ability to manage branches.

![jupyter-git repo cloning interface](img/jupyter-git_clone.png)

![jupyter-git repo tracking interface](img/jupyter-git_track.png)