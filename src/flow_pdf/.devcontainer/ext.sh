EXT_LIST="ms-python.python humao.rest-client github.copilot christian-kohler.path-intellisense esbenp.prettier-vscode redhat.vscode-yaml matangover.mypy donjayamanne.python-environment-manager ms-python.vscode-pylance formulahendry.code-runner ritwickdey.liveserver" && \
    for EXT in $EXT_LIST; do code --install-extension $EXT; done