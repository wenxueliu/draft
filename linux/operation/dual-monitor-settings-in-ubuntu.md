Dual monitor settings in Ubuntu are clumsy at best. I have tried set ups on numerous machines and I find the most reliable method is to change the monitors.xml file. For more information on monitors.xml, check out the Ubuntu Wiki on Resolutions.

First of all lets open up a terminal:

Ctrl + Alt + T

Now lets navigate to the folder where monitors.xml is stored:

cd ~/.config

You need to open the file in a text editor, we’ll use Ubuntu’s native editor, gedit:

gedit monitors.xml

Choosing your primary monitor

You will have something like the text below. There is only 2 words that you will have to change in the file, possibly 3.  (the <……..> is for display purposes only, you will have a few more lines of content in there)

<monitors version="1">
  <configuration>
      <clone>no</clone>
      <output name="DVI-0">
          <........>
          <primary>yes</primary>
      </output>
      <output name="DIN">
      </output>
      <output name="DVI-1">
          <........>
          <primary>no</primary>
      </output>
  </configuration>
</monitors>

    First make sure that the clone tag says “no” – <clone>no</clone>. if you don’t have this line, create it on the third line.
    Next, make sure the <primary>yes</primary> is on the correct output. If it isn’t change it, but make sure you change the other to “no” as above.

Now restart your computer or restart X and it will load up with the correct monitor settings.

NOTE – This will only take effect after you have logged in. LightDM has its own monitor settings (that I will be posting soon).
Setting monitor positions

Monitors.xml also specifies the position of your monitors.

The <x> and <y> values determine the position. They are based on the distance from the top left corner of the screen and are measured in pixels.

This set up includes a 22 inch monitor on the left, and 17 inch monitor on the right.

<monitors version="1">
  <configuration>
      <clone>no</clone>
      <output name="DVI-0">
          <vendor>MAX</vendor>
          <product>0x089a</product>
          <serial>0x00000b3e</serial>
          <width>1680</width>
          <height>1050</height>
          <rate>60</rate>
          <x>0</x>
          <y>0</y>
          <rotation>normal</rotation>
          <reflect_x>no</reflect_x>
          <reflect_y>no</reflect_y>
          <primary>yes</primary>
      </output>
      <output name="DIN">
      </output>
      <output name="DVI-1">
          <vendor>HWP</vendor>
          <product>0x264b</product>
          <serial>0x01010101</serial>
          <width>1280</width>
          <height>1024</height>
          <rate>0</rate>
          <x>1680</x>
          <y>0</y>
          <rotation>normal</rotation>
          <reflect_x>no</reflect_x>
          <reflect_y>no</reflect_y>
          <primary>no</primary>
      </output>
  </configuration>
</monitors>

As you can see above, the first output device (or monitor!) has an <x> value of 0 (<x> is the horizontal position). The second output has an <x> value of 1680, which is equal to the <width> of the first output. This positions the secondary monitor 1680 pixels from the left – on the seam of the first monitor.

If you have some height differences in the position of your monitor you would need to edit the <y> value of the appropriate monitor.

As with any changes to this file, you will need to restart your computer or restart X  to make these corrections apply. They will take effect after you have logged in as LightDM has its own monitor settings (coming soon).
Change dual monitor resolutions

You can see a complete version of the monitors.xml above, but the only part needed here is this:

  <width>1680</width>
  <height>1050</height>

These 2 lines set the resolution for the output devices (your dual monitors!). Set them appropriately for each of your devices. Sometimes your proprietary graphics drivers/software will fail to modify this file causing some conflicts. You should change this to match any settings you are specifying elsewhere.

Remember to restart your computer or restart X  to make these corrections apply.
