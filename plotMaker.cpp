#include <cstdlib>
#include <iostream>
#include <fstream>
#include <string>
#include <string.h>
#include <stdio.h>
#include <vector>

#define COMMA_MAX 6

using namespace std; 

ofstream plot1m;
ofstream plot500k;
ofstream plot100k;
ofstream plot1k;
ofstream plot250;


ofstream sortedAlexa;

ifstream namecoinData;
ifstream alexaData;

string breakString(string line, int number) {

    if(number < 1 || number > COMMA_MAX) {
        return "";
    }
    int index;
    int commasFound = 0;
    int insideQuotes = 0;
    int startIndex = 0;
    int endIndex = 0;
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

string breakAlexa(string line, int number) {

    int index;    
    int commaLocation;
    for(index = 0; index < line.length(); index++) { 
        if(line.at(index) == ',') {
            commaLocation = index;
            break;
        }
    }
    if(number == 1) {
        return line.substr(0, commaLocation);
    }
    return line.substr(commaLocation+1, line.length() - commaLocation-1);

}

string removeHighLevelDomain(string line) {

    int index;    
    int dotLocation=0;
    for(index = 0; index < line.length(); index++) { 
        if(line.at(index) == '.') {
            dotLocation = index;
            break;
        }
    }
    return line.substr(0, dotLocation);
}

string clearD(string line) {
    if(line.length()>=2) {
        return line.substr(2,line.length());
    }
    return "";
}

vector<string> sort(vector<string> Lhalf, vector<string> Rhalf){
//merge sort. -.-

    if(Lhalf.size() >1) {
        int midpoint = (int)Lhalf.size()/2;
        vector<string> LLhalf;
        vector<string> RLhalf;
        for(int i=0; i<Lhalf.size(); i++) {
            if(i<midpoint) {
                LLhalf.push_back(Lhalf[i]);
            }
            else{
                RLhalf.push_back(Lhalf[i]);
            }
        }
        Lhalf = sort(LLhalf, RLhalf);
    }
    if(Rhalf.size() >1) {
        int midpoint = (int)Rhalf.size()/2;
        vector<string> LRhalf;
        vector<string> RRhalf;
        for(int i=0; i<Rhalf.size(); i++) {
            if(i<midpoint) {
                LRhalf.push_back(Rhalf[i]);
            }
            else{
                RRhalf.push_back(Rhalf[i]);
            }
        }
        Rhalf = sort(LRhalf, RRhalf);
    }
  
    vector<string> solution; 
    int Lindex =0;
    int Rindex =0;
    while(Lindex < Lhalf.size() || Rindex < Rhalf.size()) {
        if(Lindex == Lhalf.size() || ((Rindex < Rhalf.size()) && (strcmp(removeHighLevelDomain(breakAlexa(Lhalf[Lindex],2)).c_str(), removeHighLevelDomain(breakAlexa(Rhalf[Rindex],2)).c_str()) > 0))) {
            solution.push_back(Rhalf[Rindex]);
            Rindex++;
        }
        else {
            solution.push_back(Lhalf[Lindex]);
            Lindex++;
        }       

    }
  //  for(int i=0; i<solution.size(); i++) {
  //      cout << solution[i] <<" ";
  //  }
  //   cout << endl;

    return solution;
            
}

string get(string key, vector<string>* list, int Lindex, int Rindex){

    //cout << "get for key: " << key << " Lindex:" << Lindex << " Rindex:" << Rindex << endl;

   // cout << "list size:" << numElements << endl;
    if((Rindex-Lindex)<=1) {
        if(removeHighLevelDomain(breakAlexa(list->at(Lindex),2)) == key) {
            return list->at(Lindex);
        }
        if(removeHighLevelDomain(breakAlexa(list->at(Rindex),2)) == key) {
            return list->at(Rindex);
        }
        return "";
    }
    int midpoint = (Rindex - Lindex)/2 + Lindex;
   // cout << "midpoint:" << midpoint << endl;
    if(removeHighLevelDomain(breakAlexa(list->at(midpoint),2)) == key) {
        return list->at(midpoint);
    }
   // cout << "list[midpoint]: " << removeHighLevelDomain(breakAlexa(list[midpoint],2)) << endl;
    if(strcmp(removeHighLevelDomain(breakAlexa(list->at(midpoint),2)).c_str(), key.c_str()) > 0) {
        return get(key, list, Lindex, midpoint);
    }
    return get(key, list, midpoint, Rindex);
}

int main() {
  
    namecoinData.open("namecoin2_tx.txt");

    plot1m.open("plot1m.txt");
    plot500k.open("plot500k.txt");
    plot100k.open("plot100k.txt");
    plot1k.open("plot1k.txt");
    plot250.open("plot250.txt");

    int totalInTop250 =0;
    int totalInTop1m =0;
    int totalInTop500k =0;
    int totalInTop100k =0;
    int totalInTop1k =0;

    string line;
    string line2;

    string blockNum;
    int activeNames=0;

    int height =0;
    int old_height=0;

    int alexaNum;
    int rank;
    string name;
    vector<string> alexa;

    alexaData.open("top-1m.csv");
    getline(alexaData, line2);
    int i=0;
    while(alexaData) {

      //  cout << line2 << endl;
        alexa.push_back(line2);
        getline(alexaData, line2);
        i=i+1;
      //  if(i > 1000){
       //     break;
       // }
    }          
    cout << "loaded alexa" << endl;
    alexaData.close();


    cout << "sorting alexa..." << endl;

    int midpoint = (int)alexa.size()/2;
    vector<string> Lhalf;
    vector<string> Rhalf;
    for(int i=0; i<alexa.size(); i++) {
        if(i<midpoint) {
            Lhalf.push_back(alexa[i]);
        }
        else{
            Rhalf.push_back(alexa[i]);
        }
    }
    alexa = sort(Lhalf, Rhalf); 

    cout << "sorted alexa" << endl;

    sortedAlexa.open("sortedAlexa.txt");
    for(int j=0; j<alexa.size(); j++) {
        sortedAlexa << alexa[j] << endl;
    }

   // cout << "got:" << get("bitcoin", alexa) << endl;

    getline(namecoinData, line);
    vector<string> namecoin;
    while(namecoinData) {
        namecoin.push_back(line);
        getline(namecoinData, line);
    }
    namecoinData.close();

    for(int j = 0; j < namecoin.size(); j++) {

        line = namecoin[j];

        height = atoi(breakString(line, 1).c_str());
        
        if(height > 215000) {
            break;
        }

        if(j%20000==0) {
            cout << (((double)height)/215000.0)*100.0 << "% done" << endl;
        }

        if(breakString(line,2) == "First" && breakString(line, 3).length() >=2 && breakString(line,3).at(0) == 'd' && breakString(line,3).at(1) == '/') {
            

            line2 = get(clearD(breakString(line,3)), &alexa, 0, alexa.size()-1);

          //  cout << line2 << endl;

            if(line2 != ""){
                name = removeHighLevelDomain(breakAlexa(line2,2));
                rank = atoi(breakAlexa(line2,1).c_str());
                
                if(clearD(breakString(line, 3)) == name) {
                    if(rank <= 250) {
                        totalInTop250++;
                    }
                    if(rank <= 1000) {
                        totalInTop1k++;
                    }
                    if(rank <= 100000) {
                        totalInTop100k++;
                    }
                    if(rank <= 500000) {
                        totalInTop500k++;
                    }
                    if(rank <= 1000000) {
                        totalInTop1m++;
                    }
                }
            }
        }
        if(height != old_height) { 
            plot250 << breakString(line,1) << " " << (((double)totalInTop250)/250.0)*100 << endl;
            plot1k << breakString(line,1) << " " << (((double)totalInTop1k)/1000.0)*100 << endl;
            plot100k << breakString(line,1) << " " << (((double)totalInTop100k)/100000.0)*100 << endl;
            plot500k << breakString(line,1) << " " << (((double)totalInTop500k)/500000.0)*100 << endl;
            plot1m << breakString(line,1) << " " << (((double)totalInTop1m)/1000000.0)*100 << endl;
            old_height = height;
        }
    }

    plot1m.close();
    plot500k.close();
    plot100k.close();
    plot1k.close();
    plot250.close();

    return 0;
}






