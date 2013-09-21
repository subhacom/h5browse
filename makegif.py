
def make_gif():
    with open('frames.txt', 'w') as fd:
        for num in range(0, 800, 10):
            fname = 'frame_%06d.png' % (num)
            fd.write('%s\n' % (fname))

if __name__ == '__main__':
    make_gif()
