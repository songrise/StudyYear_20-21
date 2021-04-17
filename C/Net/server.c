#include <sys/types.h>
#include <sys/socket.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <arpa/inet.h>
#include <signal.h>
#include <sys/wait.h>

#define PORT 9990
#define SIZE 1024

int Creat_socket() //�����׽��ֺͳ�ʼ���Լ���������
{
    int listen_socket = socket(AF_INET, SOCK_STREAM, 0); //����һ������������׽���
    if (listen_socket == -1)
    {
        perror("socket");
        return -1;
    }
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));

    addr.sin_family = AF_INET;                /* Internet��ַ�� */
    addr.sin_port = htons(PORT);              /* �˿ں� */
    addr.sin_addr.s_addr = htonl(INADDR_ANY); /* IP��ַ */

    int ret = bind(listen_socket, (struct sockaddr *)&addr, sizeof(addr)); //����
    if (ret == -1)
    {
        perror("bind");
        return -1;
    }

    ret = listen(listen_socket, 5); //����
    if (ret == -1)
    {
        perror("listen");
        return -1;
    }
    return listen_socket;
}

int wait_client(int listen_socket)
{
    struct sockaddr_in cliaddr;
    int addrlen = sizeof(cliaddr);
    printf("Waiting for client \n");
    int client_socket = accept(listen_socket, (struct sockaddr *)&cliaddr, &addrlen); //����һ���Ϳͻ��˽������׽���
    if (client_socket == -1)
    {
        perror("accept");
        return -1;
    }

    printf("Received from client %s\n", inet_ntoa(cliaddr.sin_addr));

    return client_socket;
}

void hanld_client(int listen_socket, int client_socket) //��Ϣ������,�����ǽ��ͻ��˴�������Сд��ĸת��Ϊ��д��ĸ
{
    char buf[SIZE];
    while (1)
    {
        int ret = read(client_socket, buf, SIZE - 1);
        if (ret == -1)
        {
            perror("read");
            break;
        }
        if (ret == 0)
        {
            break;
        }
        buf[ret] = '\0';
        int i;
        for (i = 0; i < ret; i++)
        {
            buf[i] = buf[i] + 'A' - 'a';
        }

        printf("%s\n", buf);
        write(client_socket, buf, ret);

        if (strncmp(buf, "end", 3) == 0)
        {
            break;
        }
    }
    close(client_socket);
}

void handler(int sig)
{

    while (waitpid(-1, NULL, WNOHANG) > 0)
    {
        printf("Child process exited\n");
    }
}

int main()
{
    int listen_socket = Creat_socket();

    signal(SIGCHLD, handler); //�����ӽ��̣���ֹ��ʬ���̵Ĳ���
    while (1)
    {
        int client_socket = wait_client(listen_socket); //����̷����������Դ����ӽ��������������̸��������
        int pid = fork();
        if (pid == -1)
        {
            perror("fork");
            break;
        }
        if (pid > 0)
        {
            close(client_socket);
            continue;
        }
        if (pid == 0)
        {
            close(listen_socket);
            hanld_client(listen_socket, client_socket);
            break;
        }
    }

    close(listen_socket);

    return 0;
}