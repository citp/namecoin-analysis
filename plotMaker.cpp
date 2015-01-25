#include <cstdlib>
#include <iostream>
#include <fstream>
#include <string>

using namespace std; 

ofstream plot;
ifstream namecoinData;

string breakString(string line, int number) {

    if(number < 1 || number > 4) {
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
    if(number == 4) {
        endIndex = line.length()-2;
    }
    return line.substr(startIndex+1, endIndex - startIndex -1);
            
            
            
}



int main() {

  
    namecoinData.open("namecoin_tx.txt");

    plot.open("plot.txt");
    string line;

    string blockNum;
    int activeNames=0;

    getline(namecoinData, line);
    while(namecoinData) {
        
        blockNum = breakString(line, 1);
        if(breakString(line, 2) == "Expired" ) {
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






