// testApp.cpp : Defines the entry point for the console application.
//

#include "stdafx.h"

#include <stdio.h>
#include <stdlib.h>
#include <Windows.h>

int getRandomNumber(int maxNum) {
	int r = rand();
	while(r > maxNum) {
		r = rand();
	}
	return r;
}

bool isValid(int correct, int choice) {
	return correct == choice;
}

int _tmain(int argc, _TCHAR* argv[])
{
	int myNum = 0;
	char inputGuessStr[512];
	ZeroMemory(inputGuessStr, sizeof(inputGuessStr));
	printf("\n\nisValid @ 0x%X\ngetRandomNumber @ 0x%X\n\n", &isValid, &getRandomNumber);
	while (true) {
		printf("Getting random number...\n");
		myNum = getRandomNumber(100);
		while(true) {
			printf("What is your guess? ");
			scanf("%500s", inputGuessStr);
			if (strcmp("next", inputGuessStr) == 0) {
				break;
			}
			if (strcmp("exit", inputGuessStr) == 0) {
				return 0;
			}
			int guess = atoi(inputGuessStr);
			if (isValid(myNum, guess)) {
				printf("Correct!\n");
				break;
			}
			if (guess < myNum) {
				printf("Higher\n");
			}
			if (guess > myNum) {
				printf("Lower\n");
			}
		}
	}
	return 0;
}

