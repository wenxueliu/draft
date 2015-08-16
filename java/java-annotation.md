#Java Annotations

Java Annotations provide information about the code and they have no direct effect on the code they
annotate. In this tutorial, we will learn about Java annotations, how to write custom annotation,
annotations usage and how to parse annotations using reflection.

Annotations are introduced in Java 1.5 and now it’s heavily used in Java frameworks like Hibernate,
Jersey, Spring. Annotation is metadata about the program embedded in the program itself. It can be
parsed by the annotation parsing tool or by compiler. We can also specify annotation availability to
either compile time only or till runtime also.

Before annotations, program metadata was available through java comments or by javadoc but annotation
offers more than that. It not only contains the metadata but it can made it available to runtime and
annotation parsers can use it to determine the process flow. For example, in Jersey webservice we add
PATH annotation with URI string to a method and at runtime jersey parses it to determine the method to
invoke for given URI pattern.

##Creating Custom Annotations in Java

Creating custom annotation is similar to writing an interface, except that it interface keyword is
prefixed with @ symbol. We can declare methods in annotation. Let’s see annotation example and then
we will discuss it’s features.

    package com.journaldev.annotations;

    import java.lang.annotation.Documented;
    import java.lang.annotation.ElementType;
    import java.lang.annotation.Inherited;
    import java.lang.annotation.Retention;
    import java.lang.annotation.RetentionPolicy;
    import java.lang.annotation.Target;

    @Documented
    @Target(ElementType.METHOD)
    @Inherited
    @Retention(RetentionPolicy.RUNTIME)
    public @interface MethodInfo{
        String author() default "Pankaj";
        String date();
        int revision() default 1;
        String comments();
    }

* Annotation methods can’t have parameters.
* Annotation methods return types are limited to primitives, String, Enums, Annotation or array of these.
* Annotation methods can have default values.

Annotations can have meta annotations attached to them. Meta annotations are used to provide information
about the annotation. There are four types of meta annotations:

**@Documented**

indicates that elements using this annotation should be documented by javadoc and similar tools. This type
should be used to annotate the declarations of types whose annotations affect the use of annotated elements
by their clients. If a type declaration is annotated with Documented, its annotations become part of the
public API of the annotated elements.

**@Target**

indicates the kinds of program element to which an annotation type is applicable. Some possible values are
TYPE, METHOD, CONSTRUCTOR, FIELD etc. If Target meta-annotation is not present, then annotation can be used
on any program element.

* ANNOTATION_TYPE 可以应用到其他注解上
* CONSTRUCTOR     可以使用到构造器上
* FIELD           可以使用到域或属性上
* LOCAL_VARIABLE  可以使用到局部变量上
* METHOD          可以使用到方法级别的注解上
* PACKAGE         可以使用到包声明上
* PARAMETER       可以使用到方法的参数上
* TYPE            可以使用到一个类的任何元素上

**@Inherited**

indicates that an annotation type is automatically inherited. If user queries the annotation type on a class
declaration, and the class declaration has no annotation for this type, then the class’s superclass will
automatically be queried for the annotation type. This process will be repeated until an annotation for this
type is found, or the top of the class hierarchy (Object) is reached.

**@Retention**

indicates how long annotations with the annotated type are to be retained. It takes RetentionPolicy argument
whose Possible values are SOURCE, CLASS and RUNTIME

* SOURCE : 表明这个注解会被编译器忽略, 并只会保留在源代码中.
* CLASS : 表明这个注解会通过编译驻留在 CLASS 文件, 但会被 JVM 在运行时忽略, 正因为如此, 其在运行时不可见.
* RUNTIME : 表示这个注解会被JVM获取, 并在运行时通过反射获取.

##Java Built-in Annotations

Java Provides three built-in annotations.

**@Override**

When we want to override a method of Superclass, we should use this annotation to inform compiler that we are
overriding a method. So when superclass method is removed or changed, compiler will show error message. Learn
why we should always use java override annotation while overriding a method.

**@Deprecated**

when we want the compiler to know that a method is deprecated, we should use this annotation. Java recommends
that in javadoc, we should provide information for why this method is deprecated and what is the alternative
to use.

**@SuppressWarnings**

This is just to tell compiler to ignore specific warnings they produce, for example using raw types in java
generics. It’s retention policy is SOURCE and it gets discarded by compiler.

**@SafeVarargs**

断言方法或者构造器的代码不会对参数进行不安全的操作. 在 Java 的后续版本中, 使用这个注解时将会令编译器产生一个
错误在编译期间防止潜在的不安全操作。

Let’s see a java example showing use of built-in annotations as well as use of custom annotation created by us
in above example.

    package com.journaldev.annotations;

    import java.io.FileNotFoundException;
    import java.util.ArrayList;
    import java.util.List;

    public class AnnotationExample {

        public static void main(String[] args) {
        }

        @Override
        @MethodInfo(author = "Pankaj", comments = "Main method", date = "Nov 17 2012", revision = 1)
        public String toString() {
            return "Overriden toString method";
        }

        @Deprecated
        @MethodInfo(comments = "deprecated method", date = "Nov 17 2012")
        public static void oldMethod() {
            System.out.println("old method, don't use it.");
        }

        @SuppressWarnings({ "unchecked", "deprecation" })
        @MethodInfo(author = "Pankaj", comments = "Main method", date = "Nov 17 2012", revision = 10)
        public static void genericsTest() throws FileNotFoundException {
            List l = new ArrayList();
            l.add("abc");
            oldMethod();
        }
    }

I believe example is self explanatory and showing use of annotations in different cases.


##Java Annotations Parsing

We will use Reflection to parse java annotations from a class. Please note that Annotation Retention Policy
should be RUNTIME otherwise it’s information will not be available at runtime and we wont be able to fetch
any data from it.

    package com.journaldev.annotations;

    import java.lang.annotation.Annotation;
    import java.lang.reflect.Method;

    public class AnnotationParsing {

        public static void main(String[] args) {
            try {
                for (Method method : AnnotationParsing.class
                        .getClassLoader()
                        .loadClass(("com.journaldev.annotations.AnnotationExample"))
                        .getMethods()) {
                    // checks if MethodInfo annotation is present for the method
                    if (method
                            .isAnnotationPresent(com.journaldev.annotations.MethodInfo.class)) {
                        try {
                            // iterates all the annotations available in the method
                            for (Annotation anno : method.getDeclaredAnnotations()) {
                                System.out.println("Annotation in Method '"
                                        + method + "' : " + anno);
                            }
                            MethodInfo methodAnno = method
                                    .getAnnotation(MethodInfo.class);
                            if (methodAnno.revision() == 1) {
                                System.out.println("Method with revision no 1 = "
                                        + method);
                            }

                        } catch (Throwable ex) {
                            ex.printStackTrace();
                        }
                    }
                }
            } catch (SecurityException | ClassNotFoundException e) {
                e.printStackTrace();
            }
        }

    }

Output of the above program is:

    Annotation in Method 'public java.lang.String com.journaldev.annotations.AnnotationExample.toString()' : @com.journaldev.annotations.MethodInfo(author=Pankaj, revision=1, comments=Main method, date=Nov 17 2012)
    Method with revision no 1 = public java.lang.String com.journaldev.annotations.AnnotationExample.toString()
    Annotation in Method 'public static void com.journaldev.annotations.AnnotationExample.oldMethod()' : @java.lang.Deprecated()
    Annotation in Method 'public static void com.journaldev.annotations.AnnotationExample.oldMethod()' : @com.journaldev.annotations.MethodInfo(author=Pankaj, revision=1, comments=deprecated method, date=Nov 17 2012)
    Method with revision no 1 = public static void com.journaldev.annotations.AnnotationExample.oldMethod()
    Annotation in Method 'public static void com.journaldev.annotations.AnnotationExample.genericsTest() throws java.io.FileNotFoundException' : @com.journaldev.annotations.MethodInfo(author=Pankaj, revision=10, comments=Main method, date=Nov 17 2012)


Reflection API is very powerful and used widely in Java, J2EE frameworks like Spring, Hibernate, JUnit, check out Reflection in Java.

That’s all for the java annotation tutorial, I hope you learned something from it.


##TODO
javax.annotation.concurrent.GuardedBy
javax.annotation.Nonnull


注解可以满足许多要求，最普遍的是：

向编译器提供信息: 注解可以被编译器用来根据不同的规则产生警告, 甚至错误. 一个例子是 Java8 中 @FunctionalInterface 注解,
这个注解使得编译器校验被注解的类, 检查它是否是一个正确的函数式接口.

文档: 注解可以被软件应用程序计算代码的质量例如:FindBugs, PMD或者自动生成报告, 例如:用来Jenkins, Jira, Teamcity.

代码生成: 注解可以使用代码中展现的元数据信息来自动生成代码或者 XML 文件, 一个不错的例子是 JAXB.

运行时处理: 在运行时检查的注解可以用做不同的目的, 像单元测试(JUnit), 依赖注入(Spring), 校验, 日志(Log4j), 数据访问(Hibernate)等等。


自定义注解:
