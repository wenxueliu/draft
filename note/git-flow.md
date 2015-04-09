
**作者** : 刘文学
**注**：本文档假设你已经对 git 有初步的认识。

###为什么是Git？

版本控制系统（VCS）经历了本地版本控制系统、集中化版本控制系统（CVCS）到分布式版本控制系统（DVCS）的发展历程，如今，分布式的高效、简单已经作为业界标配。作为一个开发者，熟练使用 git 进行开发已经是一个基本功，因为 git 的的确确改变了人们考虑合并及分支的方式。

简单介绍下工具后，让我们来看开发模型。我讲介绍的模型本质上只是一组步骤，每个团队成员都必须遵循这些步骤以形成一个可靠管理的软件开发过程。本文不会讲述任何项目的细节，只会涉及到分支策略和发布管理。

**Note**

    git 分为远程仓库和本地仓库，远程仓库只有 master 和 develop 分支，开发者从远程仓库 clone 到本地之后，下面主要讨论代码 clone 到本地的仓库后的问题。


##git 开发模型概览
![enter image description here][1]

上图是一个总体的展示。下面会将这个图进行一一分解，当你看完本文，只看此图就能理顺开发流程，视为你已经掌握 git 开发流程。

##去中心化但仍然保持中心化
![enter image description here][2]

每个开发者都对 origin 做 push 和 pull 操作。不过除了这种中心化的 push-pull 关系外，每个开发者还可以从其他开发者或者小组处 pull 变更。例如，可能两个或更多的开发者一起开发一个大的特性，在往 origin 永久性的 push 工作代码之前，他们之间可以执行一些去中心化的操 作。

在上图中，分别有 alice 和 bob、alice 和 david、clair 和 david 这些小组。从技术上来说，alice 定义一个 git remote，名字为 bob，指向bob的仓库，反过来也一样。

##主要分支

![http://www.juvenxu.com/wp-content/uploads/2010/11/git-branch-3.png][3]

中心仓库包含了两个主要分支：

* master
* develop

这两个分支始终存在，每个 Git 用户都应该熟悉 origin 上的 master 分支。与 master分支平行存在的，是另外一个名为develop的分支。

我们认为 origin/develop 分支上的 HEAD 源码反映了开发过程中最新的提交变更。当 develop 分支上的源码到达一个稳定的状态时，就可以发布版本。所有 develop 上的变更都应该以某种方式合并回 master 分支，并且使用发布版本号打上标签。稍后我们会讨论具体操作细节。

因此，每次有变化被合并到 master 分支时，根据定义这就是一次新的产品版本发布。我们趋向于严格遵守该规范，所以理论上来说，每次 master 有提交时，我们将使用一个 hook 脚本来自动构建并部署软件至产品环境服务器。

补充：
1. orign/develop 和 orign/master 分支在git服务器上面，每个开发需要git clone  url 来得到服务器的代码。然后 git checkout develop, 开始后续的操作。
2. git中的代码必须具有权限管理，比如只有指定负责人才可以修改master分支。所有开发者都可以将自己的代码merge 到 develop，然后 push 到 git 服务器。开发过程只关注 develop 分支。

##支持性分支

紧接着 master 和 develop，我们的开发模型使用多种支持性分支来帮助团队成员间实现并行开发、追踪产品特性、准备产品版本发布、以及快速修复产品问题。与主要分支不同的是，这些分支的寿命是有限的，它们最终都会被删除。

我们会用到的分支有这几类：

* 特性分支（feature branch） 
* 发布分支（release branch）
* 热补丁分支（hotfix branch）

上述每种分支都有特定的用途，它们各自关于源自什么分支、合并回什么分支，都有严格的规定（稍后我们逐个进行介绍）。

从技术角度来说，这些分支一点都不特殊。分支按照我们对其的使用方式进行分类。技术角度它们都一样是平常的Git分支。

###特性分支

![enter image description here][4]

* 分支来源：develop
* 必须合并回：develop
* 分支命令约定：Topic_[Fearure]_[Creater]（暂定） 

特性分支是用来为下一发布版本开发新特性。当开始开发一个特性的时候，该特性会成为哪个发布版本的一部分，往往还不知道。特性分支的重点是，只要特性还在开发，该分支就会一直存在，不过它最终会被合并回develop分支（将该特性加入到发布版本中），或者被丢弃（如果试验的结果令人失望），这也是特性分支存在的必要性。

特性分支往往只存在于开发者的仓库中，而不会出现在origin。

####特性开发流

开始开发新特性的时候，从develop分支创建特性分支。

    $ git checkout -b myfeature develop
    Switch to a new branch “myfeature”
    
完成的特性应该被合并回develop分支以将特性加入到下一个发布版本中：
    
    $git checkout develop
    Switch to branch ‘develop’
    $ git merge –no-ff myfeature
    Updating ea1b82a..05e9557
    (Summary of changes)
    $ git branch -d myfeature
    Deleted branch myfeature (was 05e9557).
    $ git push origin develop
    
上述代码中的 `–no-ff` 标记会使合并永远创建一个新的 commit 对象，即使该合并能以 [fast-forward][1] 的方式进行。这么做可以避免丢失特性分支存在的历史信息，同时也能清晰的展现一组 commit 一起构成一个特性。比较下面的图：

![enter image description here][5]

在第2张图中，已经无法一眼从 git 历史中看到哪些 commit 对象构成了一个特性——你需要阅读日志以获得该信息。在这种情况下，回退（revert）整个特性（一组 commit）就会比较麻烦，而如果使用了 –no-diff 就会简单很多。这么做会造成一些（空的）commit对象，但这么做是利大于弊的。

**Note**

    为了防止 git merge中忘记 --no-ff参数， 可以在git仓库的.git/config 文件里面进行别名设置.
    [alias]
        merge = merge --no-ff
    
    当然，如果你想在所有的仓库中都使用相同的别名。就在bashrc中设置
    alias='git ' //注意后面的空格不可省略
    merge='merge --no-ff'

###发布分支

* 分支来源：develop
* 必须合并回：develop和master
* 分支命名约定：rc-[VersionNume]

发布分支为准备新的产品版本发布做支持。它允许你在最后时刻检查所有的细节。此外，它还允许你修复小 bug 以及准备版本发布的元数据（例如版本号，构建日期等等）。在发布分支做这些事情之后，develop 分支就会显得比较干净，也方便为下一大版本发布接受特性。

从 develop 分支创建发布分支的时间通常是 develop 分支（差不多）能反映新版本所期望状态的时候。至少说，这是时候版本发布所计划的特性 都已经合并回了develop分支。而未来其它版本发布计划的特性则不应该合并，它们必须等到当前的版本分支创建好之后才能合并。

正是在发布分支创建的时候，对应的版本发布才获得一个版本号——不能更早。在该时刻之前，develop分支反映的是“下一版本”的相关变更，但不知道这“下一版本”到底会成为 0.3 还是 1.0，直到发布分支被创建。版本号是在发布分支创建时，基于项目版本号规则确定的。

**开始一个版本发布** 

发布分支从develop分支创建。例如，假设1.1.5是当前的产品版本，同时我们即将发布下个版本。develop 分支的状态已经是准备好“下 一版本”发布了，我们也决定下个版本是 1.2（而不是1.1.6或者2.0）。因此我们创建发布分支，并且为其赋予一个能体现新版本号的名称：

    $ git checkout -b releases-1.2 develop
   
    $ ./bump-version.sh 1.2
    
    $ git commit -a -m “Bumped version number to 1.2”
    
创建新分支并转到该分支之后，我们设定版本号。这里的bump-version.sh是一个虚构的shell脚本，它修改一些本地工作区的文件以体现新的版本号。（当然这也可以手动完成——这里只是说要有一些文件变更）接着，提交新版本号。
新的发布分支可能存在一段时间，直到该版本明确对外交付。这段时间内，该分支上可能会有一些bug的修复（而不是在develop分支上）。在该分支上添加新特性是严格禁止的。新特性必须合并到develop分支，然后等待下一个版本发布。

补充：
只有指定负责人才可以创建及修改release分支

**结束一个发布分支**

当发布分支达到一个可以正式发布的状态时，我们就需要执行一些操作。首先，将发布分支合并至 master（记住，我们之前定义 master 分支上的每一个 commit 都对应一个新版本）。接着，master分支上的 commit 必须被打上标签（tag），以方便将来寻找历史版本。最后，发布分支上的 变更需要合并回 develop，这样将来的版本也能包含相关的bug修复。

    $ git checkout master
 
    $ git merge –no-ff release-1.2
   
    $ git tag -a 1.2
    
现在版本发布完成了，而且为未来的查阅提供了标签。

为了能保留发布分支上的变更，我们还需要将分支合并回develop。在 git 中：

    $ git checkout develop
    
    $ git merge –no-ff release-1.2

这一操作可能会导致合并冲突（可能性还很大，因为我们改变了版本号）。如果发现，则修复之并提交。

现在工作才算真正完成了，最后一步是删除发布分支，因为我们已不再需要它：

    $ git branch -d release-1.2

###热补丁分支

* 可能的分支来源：master
* 必须合并回：develop和master
* 分支命名约定：hotfix-*

热补丁分支和发布分支十分类似，它的目的也是发布一个新的产品版本，尽管是不在计划中的版本发布。当产品版本发现未预期的问题的时候，就需要理解着 手处理，这个时候就要用到热补丁分支。当产品版本的重大bug需要立即解决的时候，我们从对应版本的标签创建出一个热补丁分支。

使用热补丁分支的主要作用是（develop分支上的）团队成员可以继续工作，而另外的人可以在热补丁分支上进行快速的产品bug修复。

####创建一个热补丁分支

热补丁分支从 master 分支创建。例如，假设 1.2 是当前正在被使用的产品版本，由于一个严重的 bug，产品引起了很多问题。同时，develop 分支还处于不稳定状态，无法发布新的版本。这时我们可以创建一个热补丁分支，并在该分支上修复问题：

    $ git checkout -b hotfix-1.2.1 master
    
    $ ./bump-version.sh 1.2.1

    $ git commit -a -m “Bumped version number to 1.2.1″

不要忘了在创建热补丁分之后设定一个新的版本号！
然后，修复bug并使用一个或者多个单独的commit提交。

    $ git commit -m “Fixed severe production problem”

####结束一个热补丁分支

修复完成后，热补丁分支需要合并回 master，但同时它还需要被合并回 develop，这样相关的修复代码才会同时被包含在下个版本中。这与我们完成发布分支很类似。
首先，更新master分支并打上标签。

    $ git checkout master
    
    $ git merge –no-ff hotfix-1.2.1
    
    $ git tag -a 1.2.1
    
提醒：你可能同时也会想要用 -s 或者 -u <key> 来对标签进行签名。

接着，将修复代码合并到develop：

    $ git checkout develop

    $ git merge –no-ff hotfix-1.2.1

这里还有个例外情况，如果这个时候有发布分支存在，热补丁分支的变更则应该合并至发布分支，而不是develop。将热补丁合并到发布分支，也意味着当发布分支结束的时候，变更最终会被合并到develop。（如果develop上的开发工作急需热补丁并无法等待发布分支完成，这时你也已经可以安全地将热补丁合并到develop分支。）

最后，删除临时的热补丁分支：

    $ git branch -d hotfix-1.2.1
    
虽然这个分支模型中没有什么特别新鲜的东西，但本文起始处的“全景图”事实上在我们的项目中起到了非常大的作用。它帮助建立了优雅的，易理解的概念模型，使得团队成员能够快速建立并理解一个公用的分支和发布过程。

**Note**

    每个人都负责自己的模块，如果需要其他人对你的开发做支持，经过商讨同意后，由其他人修改他的代码来支持你，即使是bug也如此。
    
    除develop master分支之外，在向git 服务器提交代码的时候要删除自建的本地分支。或者git 服务器要有控制分支的权限控制。

远程仓库

    每次 push 之前都要先 pull
    在向git 服务器提交代码的时候要删除自建的本地分支。

##QA
为什么需要 master 和 develop 分支？
    
    master 和 develop 分别表示不同的release milestones，master 表示即将发布的 milestones， 而 develop 容许团队继续向下一个 miletone 推进。

为什么需要 feature 分支？
    
    一个特性如果成功将被合并到 develop， 但是失败，我们可以不合并入 develop。如果没有，那么如果 feature 失败，我们要 revert。

为什么需要 release 分支？
为什么需要 hotfix 分支？

##参考

http://nvie.com/posts/a-successful-git-branching-model/  原文
http://www.juvenxu.com/2010/11/28/a-successful-git-branching-model/   译文
https://github.com/nvie/gitflow  git-flow 脚本
http://jeffkreeftmeijer.com/2010/why-arent-you-using-git-flow/ git 脚本使用介绍，后面的评论值得一看
http://www.cnblogs.com/taowen/archive/2012/02/28/2372330.html  国内团队的亲身经历在此支持了下面模型的正确性 
http://yedingding.com/2013/09/11/practical-git-flow-for-startups.html  这也是国内团队的亲身经历一个例子也支持了下面模型的正确性 
