#include <stdio.h>
#include <fcntl.h>
#include <termios.h>
#include <errno.h>
 
#define baudrate	B500000
  
int main(int argc, char *argv[])
{
	if (argc != 2) 
	{
		printf("Serial port wasn't provided!\n");
		return 1;
	}

	int usbdev;
	struct termios options;
 
	usbdev = open(argv[1], O_RDWR | O_NOCTTY | O_NDELAY);
 
	if (usbdev == -1)
		perror("open_port : Unable to open:");
 
	tcgetattr(usbdev, &options);
 
	cfsetispeed(&options, baudrate);
	cfsetospeed(&options, baudrate);
 
	options.c_cflag |= CS8;
	options.c_iflag |= IGNBRK;
	options.c_iflag &= ~( BRKINT | ICRNL | IMAXBEL | IXON);
	options.c_oflag &= ~( OPOST | ONLCR );
	options.c_lflag &= ~( ISIG | ICANON | IEXTEN | ECHO | ECHOE | ECHOK | ECHOCTL | ECHOKE);
	options.c_lflag |= NOFLSH;
	options.c_cflag &= ~CRTSCTS;
 
	tcsetattr(usbdev, TCSANOW, &options);
 
	return 0;
}
