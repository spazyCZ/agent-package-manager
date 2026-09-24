import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  title: 'Components/Button',
  component: Button,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'danger'],
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    label: 'Install Package',
    variant: 'primary',
  },
};

export const Secondary: Story = {
  args: {
    label: 'Cancel',
    variant: 'secondary',
  },
};

export const Danger: Story = {
  args: {
    label: 'Remove Package',
    variant: 'danger',
  },
};

export const Disabled: Story = {
  args: {
    label: 'Publishing…',
    variant: 'primary',
    disabled: true,
  },
};
