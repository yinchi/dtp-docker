#!/usr/bin/env bash
# Set up useful aliases and shell functions

git config alias.root 'rev-parse --show-toplevel'
git config alias.st 'status -sb -uall --ahead-behind'

alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'

alias e='eza -lhog -F --group-directories-first --no-permissions --smart-group'
