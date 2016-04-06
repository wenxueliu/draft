

###Java Serializer

ApacheUtils
kyro
FSH


        try (ByteArrayOutputStream bos = new ByteArrayOutputStream();
            ObjectOutput out = new ObjectOutputStream(bos)) {
            out.writeObject(this);
            return bos.toByteArray();
        } catch (IOException e) {
            System.out.println("writeTo error:" + e.getMessage());
        }


        try (ByteArrayInputStream bis = new ByteArrayInputStream(bytes);
            ObjectInput in = new ObjectInputStream(bis)) {
            return (Link)in.readObject();
        } catch(IOException e) {
            System.out.println("readFrom error:" + e.getMessage());
        } catch (ClassNotFoundException e) {
            System.out.println("readFrom error:" + e.getMessage());
        }
        return null;





##参考
https://github.com/eishay/jvm-serializers
