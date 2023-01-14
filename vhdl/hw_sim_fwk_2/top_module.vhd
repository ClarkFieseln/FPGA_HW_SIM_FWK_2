library ieee;
use ieee.std_logic_1164.ALL;


-- top_module just "passes through" signals to and from modMCounter, switch_leds and dio modules.
-- No additional logic here besides making sure that the intermediate signals are updated
-- only on the rising edge of the clock or on reset.
-- TODO: we may need to pass through "asynchronouse" DOs and LEDs
-- The sender and receivers from these signals are the Hardware Simulation Framework and the Testbench.
-- ####################################################################################################
entity top_module is
    generic(
        -- modMCounter:
        M           : integer := 5; -- count from 0 to M-1
        N           : integer := 3; -- N bits required to count upto M i.e. 2**N >= M
        -- switch_leds
        NR_SWITCHES : integer := 2;
        NR_BUTTONS  : integer := 2;
        NR_LEDS     : integer := 2;
        -- dio
        NR_DIS      : integer := 2;
        NR_DOS      : integer := 2
    );
    port(
        -- common
        reset_in          : in  std_logic;
        clock_in          : in  std_logic;
        -- modMCounter:         
        complete_tick_out : out std_logic;
        count_out         : out std_logic_vector(N - 1 downto 0);
        -- switch_leds:
        switch_in         : in  std_logic_vector(NR_SWITCHES - 1 downto 0);
        button_in         : in  std_logic_vector(NR_BUTTONS - 1 downto 0);
        led_out           : out std_logic_vector(NR_LEDS - 1 downto 0);
        -- dio:
        di_in             : in  std_logic_vector(NR_DIS - 1 downto 0);
        do_out            : out std_logic_vector(NR_DOS - 1 downto 0)        
    );
end top_module;

architecture Behavioral of top_module is
    -- signals common to both modules
    signal clock_tm, reset_tm : std_logic;
    -- signals modMCounter
    signal complete_tick_tm   : std_logic;
    signal count_tm           : std_logic_vector(N - 1 downto 0);
    -- signals switch_leds  
    signal led_tm             : std_logic_vector(NR_LEDS - 1 downto 0);
    signal switch_tm          : std_logic_vector(NR_SWITCHES - 1 downto 0);
    signal button_tm          : std_logic_vector(NR_BUTTONS - 1 downto 0);
    -- signals dio
    signal do_tm              : std_logic_vector(NR_DOS - 1 downto 0);
    signal di_tm              : std_logic_vector(NR_DIS - 1 downto 0);
begin
    -- instantiate modMCounter
    -- #######################    
    modMCounter_inst : entity work.modMCounter
        generic map(
            M => M,
            N => N
        )
        port map(
            clock         => clock_tm,
            reset         => reset_tm,
            complete_tick => complete_tick_tm,
            count         => count_tm
        );
    -- instantiate switch_leds_unit
    -- ############################
    switch_leds_unit : entity work.switch_leds
        generic map(
            NR_SWITCHES => NR_SWITCHES,
            NR_BUTTONS  => NR_BUTTONS,
            NR_LEDS     => NR_LEDS
        )
        port map(
            -- in
            reset  => reset_tm,
            clock  => clock_tm,
            switch => switch_tm,
            button => button_tm,
            -- out
            led    => led_tm
        );
    -- instantiate dio
    -- ###############
    dio_unit : entity work.dio
        generic map(
            NR_DIS => NR_DIS,
            NR_DOS => NR_DOS
        )
        port map(
            -- in
            reset  => reset_tm,
            clock  => clock_tm,
            di     => di_tm,            
            -- out
            do     => do_tm
        );        
    -- common process
    -- Note:
    --      in this process we put everything together.
    --      Alternatively, we could move async and sync behavior of modMCount, switch_leds and dio
    --      to separate processes with corresponding sensitivity lists.
    --      Both solutions generate the same circuits but the readability varies.
    --      The current approach focuses on the fact that we have a top_module which
    --      under normal conditions would add some logic to the design.
    -- ###########################################################################################
    proc_common : process(clock_in, reset_in, di_in(NR_DIS - 1 downto NR_DIS/2)) -- , switch_in, button_in)
    begin
        -- in common
        clock_tm <= clock_in;
        reset_tm <= reset_in;
        if reset_in = '1' then
            count_out         <= (others => '0');
            complete_tick_out <= '0';
            switch_tm         <= (others => '0');
            button_tm         <= (others => '0');
            led_out           <= (others => '0');
            di_tm             <= (others => '0');
            do_out            <= (others => '0');
        elsif rising_edge(clock_in) then
            complete_tick_out <= complete_tick_tm;
            count_out         <= count_tm;
            switch_tm         <= switch_in;           
            button_tm         <= button_in;
            led_out           <= led_tm;
            di_tm             <= di_in;
            do_out            <= do_tm;
        -- asynchronous DIs
        elsif rising_edge(di_in(NR_DIS - 1)) then
            di_tm(NR_DIS - 1) <= di_in(NR_DIS - 1); 
        elsif rising_edge(di_in(NR_DIS - 2)) then
            di_tm(NR_DIS - 2) <= di_in(NR_DIS - 2); 
        elsif rising_edge(di_in(NR_DIS - 3)) then
            di_tm(NR_DIS - 3) <= di_in(NR_DIS - 3); 
        elsif rising_edge(di_in(NR_DIS - 4)) then
            di_tm(NR_DIS - 4) <= di_in(NR_DIS - 4);     
        elsif rising_edge(di_in(NR_DIS - 5)) then
            di_tm(NR_DIS - 5) <= di_in(NR_DIS - 5);
        end if;
    end process proc_common;
end Behavioral;

