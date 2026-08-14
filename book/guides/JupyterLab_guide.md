# JupyterLab Guide

## Python 3 Notebook interface

### Basic Jupyter notebook manipulation

A Jupyter notebook is comprised of cells. There are 3 types of cells: raw, markdown, and code. Most likely, you will interact mainly with code and markdown cells. Visually, a code cell is distinguished from the markdown cell by a gray background. The markdown cell is used for displaying richly-formatted texts, while code cell is used to execute python codes.

In general, there are two modes of operation when working with a Jupyter notebook: the **command mode** and the **edit mode**. The former is for cell-level operations while the latter is for editing the content within a cell. If you see a flashing cursor in your notebook, you are likely in the edit mode. In addition, the current cell being edited is usually indicated by a tight blue line frame, whereas in command mode the blue frame extends all the way to the left.

A few operations that are useful in command mode:
+ `m` converts the current cell into a markdown cell
+ `y` converts the current cell into a code cell
+ `a` inserts a cell above the current cell
+ `b` inserts a cell below the current cell
+ `c` copies the content of the current cell, and `v` pastes it
+ `d` + `d` deletes the current cell
+ `z` undoes the previous action

### Running code in Jupyter notebook

Texts inside a code cell are intended to be executed as python code. To run the codes in the current cell, press `Shift` + `Enter` in *either* edit mode or command mode. You can also use the play button (`⯈`) on the top of the main panel to execute the current cell.

Importantly, the python backend ("kernel") cares only about the order you **execute the codes**, not the order they are presented in the notebook. Thus, it can be useful to occasionally restart the kernel and rerun your codes sequentially. To restart the kernel, use the refresh button (`⟳`) on the top of the main panel. You may also find the restart and run all option (`⏩`) useful, particularly before you submit your Jupyter notebook in homework, activities, etc.

### Markdown formatting

In a markdown cell certain characters have special meaning. Some useful examples:

+ To create a list, start the line with a `+`, followed by a space
+ To set a block of texts in boldface, surround the block with a pair of `**`
+ To italicize a block of texts, surround the block with a pair of `_`
+ To set a block of text in monospace, surround the block with a pair of `` ` ``
+ To create headings, start the line with a sequence of `#`, followed by a space (the more `#` the lower the heading in the hierarchy)

## Terminal interface

The Terminal interface basically brings up a user linux Terminal. Thus, the usual linux commands all work as expected, including:

+ `ls` for listing contents of a directory
+ `cd` for changing directory
+ `cp` for file copy
+ `mv` for file move
+ `rm` for file removal
+ `mkdir` for making new directory

A number of Linux programs are also installed in the environment. Notably,

+ `git` for git version control (for more details, see the [Git and GitHub Guide](./git_github_guide.md))
+ `aws s3` for managing Amazon s3 bucket (for more details, see the [Data/Code Storage Guide](./storage_guide.md))
