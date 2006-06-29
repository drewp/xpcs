from __future__ import division
import atexit, sys, time
from louie import dispatcher
sys.path.append("/home/drewp/projects/light9/light9/io")
try:
    import parport
    parport.getparport()
except ImportError:
    class _:
        def outdata(self, *args):
            pass
    parport = _()

class Ctl:
    def __init__(self):
        self.blade = False
        self.xpos = 0
        self.ypos = 0

        dispatcher.connect(self.dragTo, "dragto")
        self.path = [] # future points to walk to
        self.lastByteTime = 0
        atexit.register(lambda: self.out(0))

    def resetPos(self):
        self.xpos = self.ypos = 0
        dispatcher.send("coords", x=self.xpos, y=self.ypos)
        self.update()

    def off(self):
        self.out(0)
        
    def dragTo(self, x, y, now=False, blade=False):
        self.path.append((x, y, blade))
        #print "drag to", x, y, len(self.path)
        dispatcher.send("new path", path=self.path)
        if now:
            while self._step():
                print "stepping now"
                pass

    def step(self, runFor=.05):
        start = time.time()
        more = True
        while time.time() - start < .05 and more:
            more = self._step()

    def _step(self):
        if not self.path:
            return False
        goal = self.path[0]
        if (self.xpos, self.ypos) == goal[:2]:
            self.path.pop(0)
            dispatcher.send("new path", path=self.path)
            return True
        self.setBlade(goal[2])
        self.move(cmp(goal[0], self.xpos),
                  cmp(goal[1], self.ypos))
        return True

    def move(self, dx, dy):
        self.xpos += dx
        self.ypos += dy
        dispatcher.send("coords", x=self.xpos, y=self.ypos)
        #print "x=%d y=%d" % (self.xpos, self.ypos)
        self.update()

    def update(self):
        byte = 0
        if self.blade:
            byte |= 0x80

        byte |= (0x01, 0x03, 0x02, 0x00)[self.xpos % 4] * 0x20
        byte |= (0x01, 0x03, 0x02, 0x00)[self.ypos % 4] * 0x04

        byte |= 0x01 # power pin
        byte |= 0x02 | 0x10 # enable dirs

        now = time.time()
#        print "%.1fms delay between bytes" % ((now - self.lastByteTime) * 1000)
        self.out(byte)
        self.lastByteTime = now
        
    def out(self, byte):
        #print hex(byte)
        parport.outdata(byte)
        time.sleep(.003)

    def toggleBlade(self):
        self.setBlade(not self.blade)
        
    def setBlade(self, which):
        self.blade = which
        if self.blade:
            # blade needs full power to go down
            self.out(0x80)
            time.sleep(.05)
        self.update()
