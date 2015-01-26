#include <cstdlib>
#include <iostream>
#include <fstream>
#include <string>

#define COMMA_MAX 6

using namespace std; 

ofstream plot;
ifstream namecoinData;

string breakString(string line, int number) {

    if(number < 1 || number > COMMA_MAX) {
        return "";
    }
    int index;
    int commasFound = 0;
    int insideQuotes = 0;
    int startIndex =0;
    int endIndex =0;
    for(index = 0; index < line.length(); index++) {
        if(insideQuotes) {
            if(line.at(index) == '\'') {
                insideQuotes = 0;
            }
        }
        else if(line.at(index) == '\'') {
            insideQuotes = 1;
        }
        else if(line.at(index) == ',') {
            commasFound++;
            if(commasFound == number-1) {
                startIndex = index;
            }
            if(commasFound == number) {
                endIndex = index;
                break;
            }
        }
    }
    if(number !=1) {
        startIndex = startIndex+2; //remove the space and '
        endIndex = endIndex -1; //remove '
    }
    if(number == COMMA_MAX) {
        endIndex = line.length()-2;
    }
    if(number == 5 || number == 6) {
        //cout << line << endl;
        startIndex = startIndex -1;
        endIndex++; //assuming 5 and 6 are pubkey_ids of form decimal('#####')
    }
    return line.substr(startIndex+1, endIndex - startIndex -1);
            
            
            
}



int main() {

  
    namecoinData.open("namecoin2_tx.txt");

    plot.open("plot.txt");
    string line;

    string blockNum;
    int activeNames=0;

    getline(namecoinData, line);
    while(namecoinData) {

        //cout << line << endl;
        //cout << "[" << breakString(line, 1) << "] [" << breakString(line, 2) << "] [";
        //cout << breakString(line, 3) << "] [" << breakString(line, 4);
        //cout << "] [" << breakString(line, 5) << "] [" << breakString(line, 6) << "]" << endl;
        
        blockNum = breakString(line, 1);
        if(breakString(line, 2) == "Renewed" && breakString(line,5) == breakString(line, 6)) {
            activeNames ++;
        }
        plot << blockNum << " " << activeNames << endl;
        if(atoi(blockNum.c_str()) >= 216000) {
            break; // cutoff to stop looking at data
        }
        getline(namecoinData, line);
    }

    plot.close();
    namecoinData.close();
    return 0;
}






