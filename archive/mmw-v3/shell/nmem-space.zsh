# Nowledge Mem Space per repository. ~/.zshrc sources this file; mmw-v3/install.sh writes that line.
#
# In a git checkout whose origin has a Space (id <owner>__<name>, lowercase), export NMEM_SPACE, so
# every Claude, Codex and Grok session started from this shell reads and writes that Space. nmem
# writes to Default, without an error, when NMEM_SPACE is empty or names no Space, so a repository
# with no Space leaves NMEM_SPACE unset rather than guessing one. A value this shell did not set
# (one MMW passes to a worker or reviewer) is left alone.
#
# It runs when the directory changes and before every prompt. A Space found is remembered for the
# shell's life. A Space not found is asked about again after 30 seconds, so a Space the setup-mmw
# skill creates while this shell is open takes effect at a prompt shortly after, not only in a new
# terminal. Asking costs one `nmem spaces show`, about a tenth of a second. MMW_NMEM_SPACE_RECHECK
# sets the 30 seconds; the install suite sets it to 0.
#
# Only a shell on a terminal runs it: a script or an agent's tool shell has no prompt to wait on
# and keeps the environment it was started with.

[ -t 0 ] && [ -t 1 ] || return 0
(( $+commands[nmem] )) || return 0

zmodload -F zsh/datetime p:EPOCHSECONDS
typeset -gA _mmw_nmem_space_found _mmw_nmem_space_missed_at
typeset -g _mmw_nmem_space_owned=""

_mmw_nmem_space_sync() {
  local origin="" id=""
  origin=$(git remote get-url origin 2>/dev/null)
  if [[ $origin =~ 'github\.com[:/]([^/]+)/([^/]+)$' ]]; then
    id="${(L)match[1]}__${(L)${match[2]%.git}}"
    if [[ -z ${_mmw_nmem_space_found[$id]} ]]; then
      if (( EPOCHSECONDS - ${_mmw_nmem_space_missed_at[$id]:-0} >= ${MMW_NMEM_SPACE_RECHECK:-30} )); then
        if nmem --json spaces show "$id" >/dev/null 2>&1; then
          _mmw_nmem_space_found[$id]=1
        else
          _mmw_nmem_space_missed_at[$id]=$EPOCHSECONDS
        fi
      fi
      [[ -n ${_mmw_nmem_space_found[$id]} ]] || id=""
    fi
  fi
  [[ -n ${NMEM_SPACE:-} && ${NMEM_SPACE} != "$_mmw_nmem_space_owned" ]] && return
  if [[ -n $id ]]; then
    export NMEM_SPACE="$id"; _mmw_nmem_space_owned="$id"
  elif [[ -n $_mmw_nmem_space_owned ]]; then
    unset NMEM_SPACE; _mmw_nmem_space_owned=""
  fi
}

autoload -Uz add-zsh-hook
add-zsh-hook chpwd _mmw_nmem_space_sync
add-zsh-hook precmd _mmw_nmem_space_sync
_mmw_nmem_space_sync
