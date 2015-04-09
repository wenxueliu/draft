KMP算法其实很简单，参考[阮一峰][6]，[jBoxer][7]，但是有人搞的很复杂，如 [july][8]，而且例子不典型（过于简单），不过好在最后直接给出了本质的理解。


通过简单的链接你一定可以通过一句话来说明白KMP算法(如果不行，多看几遍这两篇文章),复杂的文章，代码可以参考，文章仅可作为参考。

###BF(Brute-Force)

    #include <stdio.h>
    #include <stdlib.h>
    #include <iostream>
    #include <string.h>
    
    using namespace std;
    //字符串匹配
    /*
    时间复杂度：
        最好 O(n)
        最差 O((n-m)*m)
    空间复杂度：O(1)
    */
    int BF(char* strS, char* strT, int pos = 0)
    {
          //返回strT在strS中第pos个字符后出现的位置。
           int i = pos;
           int j = 0;
           int k = 0; 
           int lens = strlen(strS);
           int lent = strlen(strT);
           cout << "lens=" << lens << endl;
           cout << "lent=" << lent << endl;
           if (NULL == strS | NULL == strT) return 0;
           if (lens < lent) return 0;
           while(i + lent <= lens && j < lent)
           {
                  if(strS[i+k] == strT[j])
                  {
                      ++j;    //模式串跳步
                      ++k;    //主串(内)跳步
                  }
                  else
                  {
                      ++i;
                      j=0;  //指针回溯，下一个首位字符
                      k=0;
                  }
           }//end i
           if(j >= lent)
           {
              return i;
           }
           else
           {
              return 0;
           }
    }//end
    
    
    
    int BF2( char *Target, char *Pattern, int pos = 0)
    {
        int TarLen = 0;        // Length of Target
        int PatLen = 0;        // Length of Pattern
    
        // Compute the length of Pattern
        while( '\0' != Pattern[PatLen] ) 
        { ++PatLen; } 
        while( '\0' != Target[TarLen] )
        {
            int TmpTarLen = TarLen;
            for(int i=0; i<PatLen; i++)
            {
                if( Target[TmpTarLen++] != Pattern[i] ) break;
                if( i == PatLen-1 )
                {
                    return TarLen;
                }
            }
            TarLen++;
        }
    }





###KMP(Knuth-Morris-Pratt) 

    typedef struct
    {
           int length;
           char str[0];
    }patternStr;
    
    typedef struct
    {
           size_t length; //include "\0"
           char str[0];
    }targetStr;
    
    //根据模式pStr的组成求其对应的next数组。
    void getNext(patternStr *pStr, int next[])
    {
        size_t len = pStr->length;
        next[0] = -1;
        size_t i = 0;
        int j = -1;
        while( i < len-1 )
        {
            if( j == -1 || pStr->str[i] == pStr->str[j] )
            {
                ++i;
                ++j;
                //next[i] = j;
                if(pStr->str[i] != pStr->str[j]) next[i] = j;
                else next[i] = next[j];
            }
            else
            {
                j = next[j];
            }
        }//end while
        cout << "next[ "<< len << " ]" << endl;
        for( i = 0; i < len; i++ )
        {
            cout << next[i] << "\t";
        }
        cout << endl;
    }//end
    
    
    int kmp(targetStr *t, patternStr *p, int next[])
    {
        int i = 0;
        int j = 0;
    
        while(i < t->length && j < t->length)
        {
            if(j == -1 || t->str[i] == p->str[j])
            {
                i++;
                j++;
            }
            else
            {
                j = next[j];
            }
        }
        if(j == p->length)
        {
            return( i-p->length );
        }
        else
        {
            return -1;
        }
    }
    
    int main()
    {
        //int rtnPos = 0;
        //char srStr[] = "abcabcabcabcdef";
        //char dstStr[] = "def";
        //char dstStr1[] = "defg";
        //int pos = BF2(srStr,dstStr,0);
        //int pos1 = BF2(srStr,dstStr1,0);
        //cout << "post: " << pos << endl;
        //cout << "post1: " << pos1 << endl;
        char srStr[] = "abcdaaabcabcd";
        char dstStr[] = "googgoogle";
        size_t ntmp_pStr_size = strlen(srStr);
        size_t ntmp_tStr_size = strlen(dstStr);
    
        size_t pLen = sizeof(patternStr) + (1 + ntmp_pStr_size)*sizeof(char);
        patternStr *strP = reinterpret_cast<patternStr*>(new char[pLen]);
        strP->length = ntmp_pStr_size;
        strcpy(strP->str,srStr);    //源串
        //strP->length = strlen(strP->str);
    
        size_t tLen = sizeof(targetStr) + (1 + ntmp_tStr_size)*sizeof(char);
        targetStr *strT = reinterpret_cast<targetStr*>(new char[tLen]);
        strT->length = ntmp_tStr_size;
        strcpy(strT->str,dstStr);     //模式串
    
        int *pNext = new int[strP->length];
        getNext(strP,pNext);
        int rtnPos = kmp(strT,strP,pNext);
        cout << rtnPos << endl;        //输出匹配位置
    
        delete []strP;
        delete []strT;
        delete []pNext;
        return 0;
    }

                    


  [1]: http://www.juvenxu.com/wp-content/uploads/2010/11/git-branch-1.png
  [2]: http://www.juvenxu.com/wp-content/uploads/2010/11/git-branch-2.png
  [3]: http://www.juvenxu.com/wp-content/uploads/2010/11/git-branch-3.png
  [4]: http://www.juvenxu.com/wp-content/uploads/2010/11/git-branch-4.png
  [5]: http://www.juvenxu.com/wp-content/uploads/2010/11/git-branch-5.png
  [6]:http://jakeboxer.com/blog/2009/12/13/the-knuth-morris-pratt-algorithm-in-my-own-words/)
  [7]: http://www.ruanyifeng.com/blog/2013/05/Knuth%E2%80%93Morris%E2%80%93Pratt_algorithm.html
  [8]: http://blog.csdn.net/v_july_v/article/details/7041827
