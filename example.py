from context import Screen, ScreenContext
import atexit

ctx = ScreenContext("/dev/ttyUSB0")
atexit.register(ctx.cleanup)

# Wait 6 seconds for the screen to boot up before we start uploading anything
ctx.sleep(6).reset_lcd().set_rotation(0)

eggs = 555
spam = 1234
while True:
    ctx.write_line("Eggs %d" % eggs)
    ctx.write_line("Spam %d" % spam).home()
    eggs = 99
    spam = 321