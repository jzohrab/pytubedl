# Works fine for single chars, but not arrow keys.

from console.utils import wait_key
t = ''
while t != 'q':
    print('hit any key, - to add dashes, or q to quit ...')
    t = wait_key()
    if (t == '-'):
        print("---------")
    else:
        print(f"char = {t}; ascii code = {ord(t)}")
