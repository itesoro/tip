_activate() {
    if [[ -z $1 ]]; then
        echo "Environment name can't be empty."
        return 1
    fi
    NEW_PROMPT_MODIFIER="($1) "
    if [[ -n $TIP_PROMPT_MODIFIER ]]; then
        export PS1="${${PS1}//${TIP_PROMPT_MODIFIER}/}"
    fi
    export PS1="${NEW_PROMPT_MODIFIER}${PS1}"
    export TIP_PROMPT_MODIFIER=$NEW_PROMPT_MODIFIER
    export TIP_ACTIVE_ENV=$1
}

_deactivate() {
    if [[ -n $TIP_PROMPT_MODIFIER ]]; then
        export PS1="${${PS1}//${TIP_PROMPT_MODIFIER}/}"
    fi
    export TIP_ACTIVE_ENV=""
}

case $1 in

    activate)
        _activate $2
        ;;

    deactivate)
        _deactivate
        ;;

    *)
        python -m tip $@
        ;;
esac