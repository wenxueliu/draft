# The following explanation may help to understand the use of the
# version number fields: current, revision, and age.
#
# Consider that there are three possible kinds of reactions from
# users of your library to changes in a shared library:
#
# 1. Programs using the previous version may use the new version as drop-in
#    replacement, and programs using the new version can also work with the
#    previous one. In other words, no recompiling nor relinking is needed.
#    In short, there are no changes to any symbols, no symbols removed,
#    and no symbols added. In this case, bump revision only, don't touch
#    current nor age.
#
# 2. Programs using the previous version may use the new version as drop-in
#    replacement, but programs using the new version may use APIs not
#    present in the previous one. In other words, new symbols have been
#    added and a program linking against the new version may fail with
#    "unresolved symbols." If linking against the old version at runtime:
#    set revision to 0, bump current and age.
#
# 3. Programs may need to be changed, recompiled, relinked in order to use
#    the new version. This is the case when symbols have been modified or
#    deleted. Bump current, set revision and age to 0.
