alias t := test
alias p:= publish

test OPTIONS="":
    ./tests/test.sh {{OPTIONS}}

publish VERSION:
    git checkout main
    git pull origin main
    git tag -a {{VERSION}}
    git push --tags
